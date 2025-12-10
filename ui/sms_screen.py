"""
PiPhone-X SMS Messaging Screen
Touch-optimized SMS interface with conversation view
"""

import tkinter as tk
from tkinter import messagebox
from typing import Optional, List, Dict
from .theme import Theme, Colors
from .components import TouchButton, ScrollableFrame, MessageBubble, KeyboardButton


class SMSScreen(tk.Frame):
    """
    SMS messaging screen with conversation list and compose view
    """
    
    def __init__(self, parent, modem, **kwargs):
        colors = Theme.colors
        super().__init__(parent, bg=colors.background, **kwargs)
        
        self.colors = colors
        self.modem = modem
        self.current_conversation = None
        self.conversations: Dict[str, List] = {}  # phone -> messages
        
        self._create_ui()
        
        # Set up modem callback for new messages
        if modem:
            modem.on_sms_received = self._on_sms_received
        
        # Start periodic SMS check as fallback
        self._last_sms_count = 0
        self._start_sms_polling()
    
    def _create_ui(self):
        """Build the SMS interface - compact for 320x480 (406px available)"""
        # Header - compact
        self.header = tk.Frame(self, bg=self.colors.surface, height=38)
        self.header.pack(fill=tk.X)
        self.header.pack_propagate(False)
        
        # Back button (hidden initially)
        self.back_btn = TouchButton(
            self.header,
            text="←",
            command=self._show_conversation_list,
            width=40,
            height=30,
            font=(Theme.FONT_FAMILY, 16)
        )
        
        # Title
        self.title_label = tk.Label(
            self.header,
            text="Messages",
            font=Theme.FONT_MEDIUM,
            bg=self.colors.surface,
            fg=self.colors.text_primary
        )
        self.title_label.pack(side=tk.LEFT, padx=10, pady=8)
        
        # New message button
        self.new_btn = TouchButton(
            self.header,
            text="+",
            command=self._new_message,
            width=40,
            height=30,
            bg=self.colors.accent_primary,
            fg=self.colors.background,
            font=(Theme.FONT_FAMILY, 18, "bold")
        )
        self.new_btn.pack(side=tk.RIGHT, padx=8, pady=4)
        
        # Refresh button
        self.refresh_btn = TouchButton(
            self.header,
            text="↻",
            command=self._manual_refresh,
            width=40,
            height=30,
            bg=self.colors.surface_light,
            fg=self.colors.text_primary,
            font=(Theme.FONT_FAMILY, 16)
        )
        self.refresh_btn.pack(side=tk.RIGHT, padx=2, pady=4)
        
        # Content area
        self.content = tk.Frame(self, bg=self.colors.background)
        self.content.pack(fill=tk.BOTH, expand=True)
        
        # Conversation list view
        self._create_conversation_list()
        
        # Conversation detail view
        self._create_conversation_view()
        
        # Compose view
        self._create_compose_view()
        
        # Load messages
        self._load_messages()
        
        # Show conversation list by default
        self._show_conversation_list()
    
    def _create_conversation_list(self):
        """Create the list of conversations"""
        self.list_frame = tk.Frame(self.content, bg=self.colors.background)
        
        # Scrollable list
        self.list_scroll = ScrollableFrame(self.list_frame)
        self.list_scroll.pack(fill=tk.BOTH, expand=True)
        
        self.conversation_items = []
    
    def _create_conversation_view(self):
        """Create the conversation detail view - compact"""
        self.convo_frame = tk.Frame(self.content, bg=self.colors.background)
        
        # Messages area (scrollable)
        self.messages_scroll = ScrollableFrame(self.convo_frame)
        self.messages_scroll.pack(fill=tk.BOTH, expand=True)
        
        # Input area - compact
        input_frame = tk.Frame(self.convo_frame, bg=self.colors.surface, height=45)
        input_frame.pack(fill=tk.X, side=tk.BOTTOM)
        input_frame.pack_propagate(False)
        
        # Text entry
        self.message_entry = tk.Entry(
            input_frame,
            font=Theme.FONT_SMALL,
            bg=self.colors.surface_light,
            fg=self.colors.text_primary,
            insertbackground=self.colors.text_primary,
            relief=tk.FLAT,
            width=25
        )
        self.message_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=6, pady=6)
        self.message_entry.bind("<Return>", lambda e: self._send_message())
        
        # Keyboard toggle button
        KeyboardButton(input_frame, self.message_entry).pack(side=tk.LEFT, padx=2)
        
        # Send button
        self.send_btn = TouchButton(
            input_frame,
            text="➤",
            command=self._send_message,
            width=40,
            height=32,
            bg=self.colors.accent_primary,
            fg=self.colors.background,
            font=(Theme.FONT_FAMILY, 14)
        )
        self.send_btn.pack(side=tk.RIGHT, padx=6, pady=6)
    
    def _create_compose_view(self):
        """Create the new message compose view - compact"""
        self.compose_frame = tk.Frame(self.content, bg=self.colors.background)
        
        # Recipient input
        recipient_frame = tk.Frame(self.compose_frame, bg=self.colors.surface)
        recipient_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(
            recipient_frame,
            text="To:",
            font=Theme.FONT_SMALL,
            bg=self.colors.surface,
            fg=self.colors.text_secondary
        ).pack(side=tk.LEFT, padx=8, pady=8)
        
        self.recipient_entry = tk.Entry(
            recipient_frame,
            font=Theme.FONT_SMALL,
            bg=self.colors.surface_light,
            fg=self.colors.text_primary,
            insertbackground=self.colors.text_primary,
            relief=tk.FLAT,
            width=22
        )
        self.recipient_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8, pady=8)
        
        # Keyboard toggle button
        KeyboardButton(recipient_frame, self.recipient_entry).pack(side=tk.LEFT, padx=4)
        
        # Message input
        message_frame = tk.Frame(self.compose_frame, bg=self.colors.background)
        message_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=8)
        
        self.compose_text = tk.Text(
            message_frame,
            font=Theme.FONT_SMALL,
            bg=self.colors.surface_light,
            fg=self.colors.text_primary,
            insertbackground=self.colors.text_primary,
            relief=tk.FLAT,
            height=4,
            wrap=tk.WORD
        )
        self.compose_text.pack(fill=tk.BOTH, expand=True)
        
        # Keyboard button for compose text
        kb_frame = tk.Frame(message_frame, bg=self.colors.background)
        kb_frame.pack(fill=tk.X, pady=2)
        KeyboardButton(kb_frame, self.compose_text).pack(side=tk.RIGHT, padx=4)
        
        # Send button
        btn_frame = tk.Frame(self.compose_frame, bg=self.colors.background)
        btn_frame.pack(fill=tk.X, pady=5)
        
        TouchButton(
            btn_frame,
            text="Send Message",
            command=self._send_composed_message,
            width=150,
            height=40,
            bg=self.colors.accent_primary,
            fg=self.colors.background,
            font=Theme.FONT_MEDIUM
        ).pack()
    
    def _show_conversation_list(self):
        """Show the conversation list"""
        self.convo_frame.pack_forget()
        self.compose_frame.pack_forget()
        self.list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.back_btn.pack_forget()
        self.title_label.config(text="Messages")
        self.new_btn.pack(side=tk.RIGHT, padx=10, pady=5)
        
        self.current_conversation = None
        self._refresh_conversation_list()
    
    def _show_conversation(self, phone_number: str):
        """Show a specific conversation"""
        self.list_frame.pack_forget()
        self.compose_frame.pack_forget()
        self.convo_frame.pack(fill=tk.BOTH, expand=True)
        
        self.current_conversation = phone_number
        self.title_label.config(text=phone_number)
        
        self.new_btn.pack_forget()
        self.back_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        self._refresh_messages()
    
    def _show_compose(self):
        """Show the compose new message view"""
        self.list_frame.pack_forget()
        self.convo_frame.pack_forget()
        self.compose_frame.pack(fill=tk.BOTH, expand=True)
        
        self.title_label.config(text="New Message")
        self.new_btn.pack_forget()
        self.back_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.recipient_entry.delete(0, tk.END)
        self.compose_text.delete("1.0", tk.END)
    
    def _load_messages(self):
        """Load messages from modem"""
        if not self.modem:
            return
        
        messages = self.modem.list_sms()
        self.conversations.clear()
        
        for msg in messages:
            sender = msg.sender
            if sender not in self.conversations:
                self.conversations[sender] = []
            self.conversations[sender].append({
                'content': msg.content,
                'timestamp': msg.timestamp,
                'is_sent': msg.status.startswith("STO")
            })
        
        self._refresh_conversation_list()
    
    def _refresh_conversation_list(self):
        """Refresh the conversation list display - compact"""
        # Clear existing items
        for widget in self.list_scroll.inner.winfo_children():
            widget.destroy()
        
        if not self.conversations:
            # No messages placeholder
            tk.Label(
                self.list_scroll.inner,
                text="No messages yet",
                font=Theme.FONT_SMALL,
                bg=self.colors.background,
                fg=self.colors.text_muted
            ).pack(pady=30)
            return
        
        for phone, messages in self.conversations.items():
            # Get latest message
            latest = messages[-1] if messages else {'content': '', 'timestamp': ''}
            
            item = tk.Frame(
                self.list_scroll.inner,
                bg=self.colors.surface,
                cursor="hand2"
            )
            item.pack(fill=tk.X, padx=3, pady=2)
            
            # Contact info - compact
            info_frame = tk.Frame(item, bg=self.colors.surface)
            info_frame.pack(fill=tk.X, padx=8, pady=6)
            
            # Phone number
            tk.Label(
                info_frame,
                text=phone,
                font=Theme.FONT_SMALL,
                bg=self.colors.surface,
                fg=self.colors.text_primary,
                anchor=tk.W
            ).pack(fill=tk.X)
            
            # Preview text
            preview = latest['content'][:35] + "..." if len(latest['content']) > 35 else latest['content']
            tk.Label(
                info_frame,
                text=preview,
                font=Theme.FONT_TINY,
                bg=self.colors.surface,
                fg=self.colors.text_secondary,
                anchor=tk.W
            ).pack(fill=tk.X)
            
            # Timestamp on right
            tk.Label(
                info_frame,
                text=latest['timestamp'][:10] if latest['timestamp'] else '',
                font=(Theme.FONT_FAMILY, 8),
                bg=self.colors.surface,
                fg=self.colors.text_muted
            ).place(relx=1.0, y=3, anchor=tk.NE)
            
            # Bind click
            item.bind("<Button-1>", lambda e, p=phone: self._show_conversation(p))
            for child in item.winfo_children():
                child.bind("<Button-1>", lambda e, p=phone: self._show_conversation(p))
                for subchild in child.winfo_children():
                    subchild.bind("<Button-1>", lambda e, p=phone: self._show_conversation(p))
    
    def _refresh_messages(self):
        """Refresh messages in current conversation"""
        if not self.current_conversation:
            return
        
        # Clear existing messages
        for widget in self.messages_scroll.inner.winfo_children():
            widget.destroy()
        
        messages = self.conversations.get(self.current_conversation, [])
        
        for msg in messages:
            bubble = MessageBubble(
                self.messages_scroll.inner,
                message=msg['content'],
                timestamp=msg['timestamp'],
                is_sent=msg['is_sent']
            )
            bubble.pack(fill=tk.X)
        
        # Scroll to bottom
        self.after(100, self.messages_scroll.scroll_to_bottom)
    
    def _new_message(self):
        """Start composing new message"""
        self._show_compose()
    
    def _send_message(self):
        """Send message in current conversation"""
        if not self.current_conversation:
            return
        
        message = self.message_entry.get().strip()
        if not message:
            return
        
        # Send via modem
        success = True
        if self.modem:
            success = self.modem.send_sms(self.current_conversation, message)
        
        if success:
            # Add to local conversation
            if self.current_conversation not in self.conversations:
                self.conversations[self.current_conversation] = []
            
            import time
            self.conversations[self.current_conversation].append({
                'content': message,
                'timestamp': time.strftime("%y/%m/%d,%H:%M:%S"),
                'is_sent': True
            })
            
            self.message_entry.delete(0, tk.END)
            self._refresh_messages()
        else:
            messagebox.showerror("Error", "Failed to send message")
    
    def _send_composed_message(self):
        """Send the composed new message"""
        recipient = self.recipient_entry.get().strip()
        message = self.compose_text.get("1.0", tk.END).strip()
        
        if not recipient:
            messagebox.showwarning("Warning", "Please enter a recipient")
            return
        
        if not message:
            messagebox.showwarning("Warning", "Please enter a message")
            return
        
        # Send via modem
        success = True
        if self.modem:
            success = self.modem.send_sms(recipient, message)
        
        if success:
            # Add to conversations
            if recipient not in self.conversations:
                self.conversations[recipient] = []
            
            import time
            self.conversations[recipient].append({
                'content': message,
                'timestamp': time.strftime("%y/%m/%d,%H:%M:%S"),
                'is_sent': True
            })
            
            # Show the conversation
            self._show_conversation(recipient)
        else:
            messagebox.showerror("Error", "Failed to send message")
    
    def _on_sms_received(self, sms):
        """Handle incoming SMS"""
        sender = sms.sender
        
        if sender not in self.conversations:
            self.conversations[sender] = []
        
        self.conversations[sender].append({
            'content': sms.content,
            'timestamp': sms.timestamp,
            'is_sent': False
        })
        
        # Refresh if viewing this conversation
        if self.current_conversation == sender:
            self._refresh_messages()
        else:
            self._refresh_conversation_list()
    
    def refresh(self):
        """Refresh all messages from modem"""
        self._load_messages()
    
    def _manual_refresh(self):
        """Manual refresh triggered by button"""
        # Visual feedback
        self.refresh_btn.set_text("...")
        self.update_idletasks()
        
        # Reload messages
        self._load_messages()
        
        # Check for new unread
        self._check_for_new_sms()
        
        # Restore button
        self.after(500, lambda: self.refresh_btn.set_text("↻"))
    
    def _start_sms_polling(self):
        """Start periodic SMS polling as fallback for notifications"""
        self._check_for_new_sms()
    
    def _check_for_new_sms(self):
        """Check for new SMS messages periodically"""
        if self.modem:
            try:
                # Get unread messages
                messages = self.modem.list_sms("REC UNREAD")
                
                if messages:
                    for msg in messages:
                        sender = msg.sender
                        
                        # Check if we already have this message
                        if sender in self.conversations:
                            existing = self.conversations[sender]
                            already_exists = any(
                                m['content'] == msg.content and 
                                m['timestamp'] == msg.timestamp 
                                for m in existing
                            )
                            if already_exists:
                                continue
                        
                        # New message! Add it
                        if sender not in self.conversations:
                            self.conversations[sender] = []
                        
                        self.conversations[sender].append({
                            'content': msg.content,
                            'timestamp': msg.timestamp,
                            'is_sent': False
                        })
                        
                        # Refresh UI
                        if self.current_conversation == sender:
                            self._refresh_messages()
                        else:
                            self._refresh_conversation_list()
                        
                        # Mark as read
                        if msg.index > 0:
                            self.modem.delete_sms(msg.index)
            except Exception as e:
                print(f"SMS check error: {e}")
        
        # Check again in 10 seconds
        self.after(10000, self._check_for_new_sms)

