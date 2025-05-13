<script>
  import { onMount, onDestroy } from 'svelte';
  import UserList from './components/UserList.svelte';
  import ChatWindow from './components/ChatWindow.svelte';

  // Application state
  let socket;
  let connected = false;
  let clientId = localStorage.getItem('chat_client_id') || crypto.randomUUID();
  let nickname = localStorage.getItem('chat_nickname') || '';
  let hasStoredNickname = !!localStorage.getItem('chat_nickname'); // Flag to know if we have a saved nickname
  let users = [];
  let selectedUser = null;
  let messages = {}; // Map of user IDs to message arrays
  let processedMessageIds = new Set(); // Track message IDs to prevent duplicates
  
  /** @type {Record<string, boolean>} */
  let unreadMessages = {}; // Track which users have unread messages
  
  // Nickname change state
  let showNicknameForm = false;
  let newNickname = '';
  
  // Save client ID to localStorage for persistence
  localStorage.setItem('chat_client_id', clientId);
  
  // Load previously stored messages from localStorage
  try {
    const storedMessages = localStorage.getItem('chat_messages');
    if (storedMessages) {
      messages = JSON.parse(storedMessages);
    }
  } catch (error) {
    console.error('Error loading stored messages:', error);
    // If there's an error parsing, just start with empty messages
    messages = {};
  }

  // Connect to WebSocket server
  onMount(() => {
    connectWebSocket();
    
    // Attempt to restore the last selected user
    try {
      const lastSelectedUserJson = localStorage.getItem('chat_last_selected_user');
      if (lastSelectedUserJson) {
        const lastUser = JSON.parse(lastSelectedUserJson);
        // We'll set this as the selected user once we confirm they still exist
        // in the users list after connection
      }
    } catch (error) {
      console.error('Error restoring last selected user:', error);
    }
  });

  onDestroy(() => {
    if (socket) {
      socket.close();
    }
  });

  function connectWebSocket() {
    // Connect to the WebSocket server
    // Dynamically determine WebSocket URL to work in both development and Docker environments
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    
    // Get the hostname (without port) from the current URL
    const hostname = window.location.hostname;
    
    // Always use port 8000 for the backend WebSocket server
    // This works both in development and in Docker
    const wsUrl = `${wsProtocol}//${hostname}:8000/ws/${clientId}`;
    
    console.log('Connecting to WebSocket:', wsUrl);
    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      connected = true;
      console.log('WebSocket connection established');
      
      // If we have a stored nickname, send it to the server right after connection
      if (nickname) {
        const message = {
          type: 'nickname_change',
          nickname: nickname
        };
        socket.send(JSON.stringify(message));
        console.log('Sent stored nickname to server:', nickname);
      }
    };

    socket.onclose = () => {
      connected = false;
      console.log('WebSocket connection closed');
      // Try to reconnect after a delay
      setTimeout(connectWebSocket, 3000);
    };

    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      } catch (e) {
        console.error('Error parsing WebSocket message:', e);
      }
    };
  }

  function handleWebSocketMessage(data) {
    console.log('Received message:', data);

    switch (data.type) {
      case 'nickname_assigned':
        // Always update clientId
        clientId = data.client_id;
        localStorage.setItem('chat_client_id', clientId);
        
        // If we already have a stored nickname, ignore the server's assignment
        if (hasStoredNickname) {
          console.log('Keeping stored nickname:', nickname);
          
          // Send our stored nickname to the server to override the generated one
          setTimeout(() => {
            if (socket && socket.readyState === WebSocket.OPEN) {
              const message = {
                type: 'nickname_change',
                nickname: nickname
              };
              socket.send(JSON.stringify(message));
              console.log('Sent stored nickname to server:', nickname);
            }
          }, 100); // Small delay to ensure message processing order
        } else {
          // No stored nickname, accept the server's assignment
          nickname = data.nickname;
          localStorage.setItem('chat_nickname', nickname);
          hasStoredNickname = true;
          console.log('Accepted new nickname from server:', nickname);
        }
        break;

      case 'users_update':
        users = data.users.filter(user => user.id !== clientId);
        
        // Try to restore the last selected user if they still exist in the users list
        try {
          const lastSelectedUserJson = localStorage.getItem('chat_last_selected_user');
          if (lastSelectedUserJson && !selectedUser) {
            const lastUser = JSON.parse(lastSelectedUserJson);
            // Find the user in the current users list
            const existingUser = users.find(u => u.id === lastUser.id);
            if (existingUser) {
              selectedUser = existingUser;
              console.log('Restored last selected user:', selectedUser.nickname);
            }
          }
        } catch (error) {
          console.error('Error finding last selected user:', error);
        }
        break;

      case 'direct_message':
        const otherUserId = data.sender_id === clientId ? data.recipient_id : data.sender_id;
        const messageId = data.message_id;
        
        // Skip messages that we sent ourselves (since we already added them locally)
        if (data.sender_id === clientId) {
          break;
        }
        
        // Check if we've already processed this message
        if (messageId && processedMessageIds.has(messageId)) {
          console.log('Skipping duplicate message:', messageId);
          break;
        }
        
        // Add this message ID to our processed set
        if (messageId) {
          processedMessageIds.add(messageId);
          
          // Keep the set to a reasonable size by removing old entries if it gets too large
          if (processedMessageIds.size > 1000) {
            // Convert to array, remove the oldest 200 items, and convert back to Set
            const idsArray = Array.from(processedMessageIds);
            processedMessageIds = new Set(idsArray.slice(200));
          }
        }
        
        // For messages from others, add them to our message list
        if (!messages[otherUserId]) {
          messages[otherUserId] = [];
        }
        
        messages[otherUserId] = [...messages[otherUserId], {
          id: messageId,
          sender_id: data.sender_id,
          content: data.content,
          timestamp: data.timestamp,
          is_mine: false, // Must be from someone else since we skip our own
          type: data.message_type || 'text' // Include message type for proper rendering
        }];
        
        messages = messages; // Trigger reactivity
        
        // Mark this user as having unread messages if they're not the currently selected user
        if (!selectedUser || selectedUser.id !== otherUserId) {
          unreadMessages[otherUserId] = true;
          unreadMessages = {...unreadMessages}; // Trigger reactivity
        }
        
        // Save updated messages to localStorage
        saveMessagesToLocalStorage();
        break;
    }
  }
  
  // Helper function to save messages to localStorage
  function saveMessagesToLocalStorage() {
    try {
      localStorage.setItem('chat_messages', JSON.stringify(messages));
    } catch (error) {
      console.error('Error saving messages to localStorage:', error);
    }
  }

  function sendMessage(content, messageType = 'text') {
    if (!selectedUser || !socket || socket.readyState !== WebSocket.OPEN) {
      return;
    }
    
    // For text messages, ensure content is not empty
    if (messageType === 'text' && !content.trim()) {
      return;
    }
    
    // Generate a unique ID for this message
    const messageId = crypto.randomUUID();
    
    // Add message to processed IDs to prevent duplicates
    processedMessageIds.add(messageId);
    
    const message = {
      type: 'direct_message',
      message_id: messageId,
      recipient_id: selectedUser.id,
      content: content,
      message_type: messageType // Include message type in the payload
    };
    
    // Immediately add message to the local messages array
    if (!messages[selectedUser.id]) {
      messages[selectedUser.id] = [];
    }
    
    messages[selectedUser.id].push({
      id: messageId,
      sender_id: clientId,
      content: content,
      timestamp: new Date().toISOString(),
      is_mine: true,
      type: messageType // Store message type for proper display
    });
    
    // Trigger reactivity
    messages = messages;
    
    // Save messages to localStorage
    saveMessagesToLocalStorage();
    
    // Send the message to the server
    socket.send(JSON.stringify(message));
  }

  function selectUser(user) {
    selectedUser = user;
    if (!messages[user.id]) {
      messages[user.id] = [];
      saveMessagesToLocalStorage(); // Make sure the empty array is saved
    }
    
    // Clear unread message notification for this user
    if (unreadMessages[user.id]) {
      unreadMessages[user.id] = false;
      unreadMessages = {...unreadMessages}; // Trigger reactivity
    }
    
    // Save the last selected user to localStorage
    try {
      localStorage.setItem('chat_last_selected_user', JSON.stringify(user));
    } catch (error) {
      console.error('Error saving selected user:', error);
    }
  }
  
  // Function to handle nickname changes
  function changeNickname() {
    if (!newNickname || !newNickname.trim() || newNickname === nickname) {
      // No change or invalid nickname
      showNicknameForm = false;
      return;
    }
    
    // Update local nickname
    nickname = newNickname.trim();
    hasStoredNickname = true;
    
    // Save to localStorage
    localStorage.setItem('chat_nickname', nickname);
    
    // Send to server if connected
    if (socket && socket.readyState === WebSocket.OPEN) {
      const message = {
        type: 'nickname_change',
        nickname: nickname
      };
      socket.send(JSON.stringify(message));
    }
    
    // Reset form
    showNicknameForm = false;
    newNickname = '';
  }
</script>

<main>
  <header>
    <h1>Simple Chat</h1>
    {#if nickname}
      <div class="user-info">
        <div class="nickname-container">
          <span>Your nickname: <strong>{nickname}</strong></span>
          <button class="edit-nickname-btn" on:click={() => showNicknameForm = !showNicknameForm}>
            {showNicknameForm ? 'Cancel' : 'Change'}
          </button>
        </div>
        <span class="connection-status {connected ? 'connected' : 'disconnected'}">
          {connected ? 'Connected' : 'Disconnected'}
        </span>
      </div>
      
      {#if showNicknameForm}
        <div class="nickname-form">
          <form on:submit|preventDefault={changeNickname}>
            <input 
              type="text" 
              bind:value={newNickname} 
              placeholder="Enter new nickname" 
              minlength="3"
              maxlength="20"
              required
            />
            <button type="submit">Save</button>
          </form>
        </div>
      {/if}
    {:else}
      <div class="connecting">Connecting...</div>
    {/if}
  </header>

  <div class="chat-container">
    <UserList {users} {selectedUser} {unreadMessages} onSelectUser={selectUser} />
    
    <ChatWindow 
      selectedUser={selectedUser} 
      currentMessages={selectedUser ? messages[selectedUser.id] || [] : []} 
      onSendMessage={sendMessage} 
    />
  </div>
</main>

<style>
  main {
    display: flex;
    flex-direction: column;
    height: 100vh;
    max-width: 1200px;
    margin: 0 auto;
    padding: 1rem;
    box-sizing: border-box;
    font-family: 'Inter', 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  }

  header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 1rem;
    border-bottom: 1px solid #333;
    margin-bottom: 1rem;
  }

  h1 {
    font-size: 1.8rem;
    margin: 0;
    color: #e1e1e1;
  }

  .user-info {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
  }
  
  .nickname-container {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .edit-nickname-btn {
    font-size: 0.8rem;
    padding: 0.25rem 0.5rem;
    background-color: #1a2e1a;
    border: 1px solid #2e7d32;
  }
  
  .nickname-form {
    margin-top: 0.5rem;
    padding: 0.75rem;
    background-color: #1a2e1a;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  }
  
  .nickname-form form {
    display: flex;
    gap: 0.5rem;
  }
  
  .nickname-form input {
    flex: 1;
    padding: 0.5rem;
    border-radius: 4px;
    border: 1px solid #2e7d32;
    background-color: #1e1e1e;
    color: #e1e1e1;
  }

  .connection-status {
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.8rem;
  }

  .connected {
    background-color: #1b4d1b;
    color: #a2e4a2;
  }

  .disconnected {
    background-color: #4d1c1c;
    color: #e4a2a2;
  }

  .connecting {
    color: #e4d7a2;
    background-color: #4d3e1c;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
  }

  .chat-container {
    display: flex;
    flex: 1;
    gap: 1rem;
    height: calc(100vh - 100px);
    overflow: hidden;
  }
</style>
