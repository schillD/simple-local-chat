<script>
  import { onMount, afterUpdate } from 'svelte';

  /**
   * @typedef {Object} User
   * @property {string} id - The unique identifier for the user
   * @property {string} nickname - The user's display name
   */
  
  /** @type {User|null} */
  export let selectedUser = null;
  /** @type {Array} */
  export let currentMessages = [];
  /** @type {function(string, string): void} */
  export let onSendMessage = (message, type = 'text') => {};

  let messageInput = '';
  let chatContainer;
  let messagesContainer;
  
  // Image modal state
  let showImageModal = false;
  let modalImageSrc = '';

  $: isReady = !!selectedUser;
  
  function openImageModal(imageSrc) {
    modalImageSrc = imageSrc;
    showImageModal = true;
  }
  
  function closeImageModal() {
    showImageModal = false;
  }

  // Auto-scroll to bottom when new messages arrive
  $: if (currentMessages) {
    scrollToBottom();
  }

  onMount(() => {
    scrollToBottom();
    
    // Add global keyboard event listener for the Escape key
    const handleKeydown = (event) => {
      if (event.key === 'Escape' && showImageModal) {
        closeImageModal();
      }
    };
    
    window.addEventListener('keydown', handleKeydown);
    
    return () => {
      window.removeEventListener('keydown', handleKeydown);
    };
  });

  afterUpdate(() => {
    scrollToBottom();
  });

  function scrollToBottom() {
    if (messagesContainer) {
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
  }

  function handleSubmit() {
    if (!messageInput.trim()) return;
    onSendMessage(messageInput, 'text');
    messageInput = '';
  }
  
  function handleImageUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    // Check if file is an image
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file');
      return;
    }
    
    // Check file size (limit to 1MB)
    if (file.size > 1024 * 1024) {
      alert('Image size should be less than 1MB');
      return;
    }
    
    const reader = new FileReader();
    reader.onload = (e) => {
      // The result is a string (base64 data URL) when using readAsDataURL
      const imageData = String(e.target.result);
      onSendMessage(imageData, 'image');
    };
    reader.readAsDataURL(file);
    
    // Reset the file input
    event.target.value = '';
  }
  
  function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    // Check file size (limit to 5MB)
    if (file.size > 5 * 1024 * 1024) {
      alert('File size should be less than 5MB');
      return;
    }
    
    const reader = new FileReader();
    reader.onload = (e) => {
      const fileData = String(e.target.result);
      // Send file with metadata
      const fileMessage = {
        name: file.name,
        type: file.type,
        size: file.size,
        data: fileData
      };
      onSendMessage(JSON.stringify(fileMessage), 'file');
    };
    reader.readAsDataURL(file);
    
    // Reset the file input
    event.target.value = '';
  }

  function formatTime(dateString) {
    try {
      const date = new Date(dateString);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch (e) {
      return '';
    }
  }
  
  function formatFileSize(bytes) {
    if (bytes < 1024) {
      return bytes + ' B';
    } else if (bytes < 1024 * 1024) {
      return (bytes / 1024).toFixed(1) + ' KB';
    } else {
      return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    }
  }
</script>

<div class="chat-window" bind:this={chatContainer}>
  {#if isReady}
    <div class="chat-header">
      <h2>Chat with {selectedUser.nickname}</h2>
    </div>
    
    <div class="messages-container" bind:this={messagesContainer}>
      {#if currentMessages.length === 0}
        <div class="empty-chat">
          <p>No messages yet</p>
          <p class="hint">Start the conversation by typing a message below</p>
        </div>
      {:else}
        <div class="messages">
          {#each currentMessages as message}
            <div class="message {message.is_mine ? 'mine' : 'theirs'}">
              <div class="message-content {message.type === 'image' ? 'image-message' : ''}">
                {#if message.type === 'image'}
                  <button 
                    class="image-button"
                    on:click={() => openImageModal(message.content)}
                    on:keydown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        openImageModal(message.content);
                        e.preventDefault();
                      }
                    }}
                    aria-label="View enlarged image"
                    title="Click to enlarge"
                  >
                    <img 
                      src={message.content} 
                      alt="Shared image" 
                      class="shared-image" 
                    />
                  </button>
                {:else if message.type === 'file'}
                  <div class="file-attachment">
                    <!-- Parse the JSON string to get file details -->
                    {#if message.content}
                      {@const fileData = JSON.parse(message.content)}
                      <div class="file-info">
                        <span class="file-icon">📎</span>
                        <div class="file-details">
                          <div class="file-name">{fileData.name}</div>
                          <div class="file-meta">{formatFileSize(fileData.size)}</div>
                        </div>
                      </div>
                      <a 
                        href={fileData.data} 
                        download={fileData.name}
                        class="download-button"
                        title="Download file"
                      >
                        Download
                      </a>
                    {/if}
                  </div>
                {:else}
                  <p>{message.content}</p>
                {/if}
                <span class="timestamp">{formatTime(message.timestamp)}</span>
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </div>
    
    <div class="message-input">
      <form on:submit|preventDefault={handleSubmit}>
        <div class="input-container">
          <input 
            type="text" 
            bind:value={messageInput} 
            placeholder="Type a message..." 
            autocomplete="off"
          />
          <div class="message-actions">
            <label class="image-upload-label" title="Upload image">
              <input 
                type="file" 
                accept="image/*" 
                on:change={handleImageUpload} 
                class="image-upload"
              />
              <span class="image-icon">📷</span>
            </label>
            <label class="file-upload-label" title="Upload file">
              <input 
                type="file" 
                on:change={handleFileUpload} 
                class="file-upload"
              />
              <span class="file-icon">📎</span>
            </label>
            <button type="submit" disabled={!messageInput.trim()}>Send</button>
          </div>
        </div>
      </form>
    </div>
  {:else}
    <div class="no-chat-selected">
      <p>Select a user to start chatting</p>
    </div>
  {/if}
  
  <!-- Image Modal -->
  {#if showImageModal}
    <!-- Modal backdrop with click handler -->
    <div 
      class="modal-backdrop"
      on:click={closeImageModal}
      on:keydown={(e) => {
        if (e.key === 'Escape') {
          closeImageModal();
        }
      }}
      tabindex="-1"
      role="presentation"
    >
      <!-- Modal dialog -->
      <div
        class="image-modal" 
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
      >
        <!-- Modal content -->
        <div 
          class="modal-content" 
          on:click|stopPropagation 
          role="document"
        >
          <button 
            class="close-button" 
            on:click={closeImageModal} 
            aria-label="Close modal"
          >
            &times;
          </button>
          <h2 id="modal-title" class="sr-only">Image Preview</h2>
          <img src={modalImageSrc} alt="" /><!-- Alt is empty because image is presentational here -->
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .chat-window {
    flex: 1;
    background-color: #1e1e1e;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    display: flex;
    flex-direction: column;
    height: 100%;
    overflow: hidden;
    color: #e1e1e1;
  }

  .chat-header {
    padding: 1rem;
    border-bottom: 1px solid #333;
  }

  .chat-header h2 {
    font-size: 1.2rem;
    margin: 0;
    color: #333;
  }

  .messages-container {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
    display: flex;
    flex-direction: column;
  }

  .empty-chat, .no-chat-selected {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: #666;
    text-align: center;
  }

  .hint {
    font-size: 0.8rem;
    color: #999;
  }

  .messages {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .message {
    display: flex;
    margin-bottom: 0.5rem;
  }

  .message.mine {
    justify-content: flex-end;
  }

  .message-content {
    max-width: 70%;
    border-radius: 16px;
    padding: 0.5rem 1rem;
    position: relative;
  }

  .message.mine .message-content {
    background-color: #2e7d32; /* Green for own messages */
    color: white;
    border-bottom-right-radius: 4px;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
  }

  .message.theirs .message-content {
    background-color: #333;
    color: #e1e1e1;
    border-bottom-left-radius: 4px;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
  }

  .message-content p {
    margin: 0;
    word-wrap: break-word;
  }

  .timestamp {
    font-size: 0.7rem;
    opacity: 0.7;
    display: block;
    text-align: right;
    margin-top: 0.25rem;
  }

  .message.mine .timestamp {
    color: rgba(255, 255, 255, 0.8);
  }

  .message-input {
    padding: 1rem;
    border-top: 1px solid #333;
    background-color: #1e1e1e;
  }

  .message-input form {
    display: flex;
    padding: 1rem;
    width: 100%;
  }
  
  .input-container {
    display: flex;
    width: 100%;
    gap: 0.5rem;
  }

  .message-input input[type="text"] {
    flex: 1;
    padding: 0.75rem;
    border-radius: 20px;
    border: 1px solid #333;
    background-color: #222;
    color: #e1e1e1;
  }
  
  .message-actions {
    display: flex;
    gap: 0.5rem;
    align-items: center;
  }
  
  .image-upload, .file-upload {
    display: none;
  }
  
  .image-upload-label, .file-upload-label {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 2.5rem;
    height: 2.5rem;
    background-color: #1a2e1a;
    border-radius: 50%;
    cursor: pointer;
    border: 1px solid #2e7d32;
    transition: background-color 0.2s;
    margin-right: 0.5rem;
  }
  
  .image-upload-label:hover, .file-upload-label:hover {
    background-color: #2e7d32;
  }
  
  .image-icon, .file-icon {
    font-size: 1.2rem;
  }
  
  .image-button {
    background: none;
    border: none;
    padding: 0;
    margin: 0;
    cursor: pointer;
    transition: transform 0.2s ease;
  }
  
  .image-button:hover, .image-button:focus {
    transform: scale(1.03);
    outline: none;
  }
  
  .image-button:focus {
    box-shadow: 0 0 0 2px #2e7d32;
    border-radius: 8px;
  }
  
  .shared-image {
    max-width: 100%;
    max-height: 300px;
    border-radius: 8px;
    margin-bottom: 0.25rem;
    display: block;
  }
  
  .image-message {
    max-width: 300px !important;
  }
  
  /* File attachment styles */
  .file-attachment {
    background-color: #222;
    border-radius: 8px;
    padding: 0.75rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    margin-bottom: 0.25rem;
    width: 250px;
  }
  
  .file-info {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }
  
  .file-details {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    overflow: hidden;
  }
  
  .file-name {
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 180px;
  }
  
  .file-meta {
    font-size: 0.8rem;
    color: #aaa;
  }
  
  .download-button {
    background-color: #2e7d32;
    color: white;
    text-decoration: none;
    padding: 0.5rem;
    border-radius: 4px;
    text-align: center;
    font-size: 0.9rem;
    transition: background-color 0.2s;
  }
  
  .download-button:hover {
    background-color: #1b5e20;
  }
  
  /* Screen reader only content */
  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border-width: 0;
  }
  
  /* Modal styles */
  .modal-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 999;
  }
  
  /* Image Modal Styles */
  .image-modal {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.8);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    padding: 2rem;
  }
  
  .modal-content {
    position: relative;
    max-width: 90%;
    max-height: 90%;
    background-color: #1e1e1e;
    border-radius: 8px;
    padding: 1rem;
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.5);
  }
  
  .modal-content img {
    display: block;
    max-width: 100%;
    max-height: 80vh;
    margin: 0 auto;
  }
  
  .close-button {
    position: absolute;
    top: -15px;
    right: -15px;
    background-color: #2e7d32;
    color: white;
    border: none;
    border-radius: 50%;
    width: 30px;
    height: 30px;
    font-size: 20px;
    line-height: 1;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1001;
  }
  
  .close-button:hover {
    background-color: #1b5e20;
  }

  input:focus {
    border-color: #2e7d32;
    box-shadow: 0 0 0 2px rgba(46, 125, 50, 0.2);
  }

  button {
    background-color: #2e7d32;
    color: white;
    border: none;
    border-radius: 24px;
    padding: 0.75rem 1.25rem;
    font-weight: 500;
    cursor: pointer;
    transition: background-color 0.2s ease;
  }

  button:hover {
    background-color: #388e3c;
  }

  button:disabled {
    background-color: #424242;
    color: #757575;
    cursor: not-allowed;
  }
</style>
