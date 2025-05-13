<script>
  /**
   * @typedef {Object} User
   * @property {string} id - The unique identifier for the user
   * @property {string} nickname - The user's display name
   */
  
  /** @type {User[]} */
  export let users = [];
  /** @type {User|null} */
  export let selectedUser = null;
  /** @type {function(User): void} */
  export let onSelectUser = (user) => {};
  /** @type {Object.<string, boolean>} */
  export let unreadMessages = {}; // Track which users have unread messages
</script>

<div class="user-list">
  <h2>Available Users</h2>
  
  {#if users.length === 0}
    <div class="no-users">
      <p>No users available</p>
      <p class="hint">Waiting for others to join...</p>
    </div>
  {:else}
    <ul role="listbox" aria-label="Available users">
      {#each users as user}
        <li
          class="user-item {selectedUser && selectedUser.id === user.id ? 'selected' : ''}"
          on:click={() => onSelectUser(user)}
          on:keydown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              onSelectUser(user);
              e.preventDefault();
            }
          }}
          tabindex="0"
          role="option"
          aria-selected={selectedUser && selectedUser.id === user.id}
        >
          <div class="user-avatar">
            {user.nickname.charAt(0).toUpperCase()}
          </div>
          <div class="user-details">
            <span class="user-nickname">{user.nickname}</span>
          </div>
          {#if unreadMessages[user.id] && (!selectedUser || selectedUser.id !== user.id)}
            <div class="notification-indicator" title="New message">•</div>
          {/if}
        </li>
      {/each}
    </ul>
  {/if}
</div>

<style>
  .user-list {
    background-color: #1e1e1e;
    border-radius: 8px;
    width: 250px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }
  
  /* Mobile responsive styles */
  @media (max-width: 768px) {
    .user-list {
      width: 100%;
      max-height: 200px;
      margin-bottom: 0.5rem;
    }
    
    .user-item {
      padding: 12px;
      font-size: 14px;
    }
    
    /* Make sure touch targets are large enough */
    li {
      min-height: 44px;
    }
  }

  h2 {
    font-size: 1.2rem;
    margin: 0 0 1rem 0;
    color: #e1e1e1;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #333;
  }

  ul {
    list-style: none;
    padding: 0;
    margin: 0;
    overflow-y: auto;
    flex: 1;
  }

  .no-users {
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

  .user-item {
    display: flex;
    align-items: center;
    padding: 0.75rem;
    margin-bottom: 0.5rem;
    border-radius: 6px;
    cursor: pointer;
    transition: background-color 0.2s ease;
  }

  .user-item:hover {
    background-color: #2c2c2c;
  }

  .user-item.selected {
    background-color: #1a3521;
    border-left: 3px solid #2e7d32;
  }

  .user-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background-color: #2e7d32;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    margin-right: 0.75rem;
  }

  .user-details {
    display: flex;
    flex-direction: column;
  }

  .user-nickname {
    font-weight: 500;
  }
  
  .notification-indicator {
    margin-left: auto;
    color: #ff9800; /* Orange color */
    font-size: 1.5rem;
    line-height: 1;
    font-weight: bold;
    animation: pulse 1.5s infinite;
  }
  
  @keyframes pulse {
    0% { opacity: 0.7; }
    50% { opacity: 1; }
    100% { opacity: 0.7; }
  }
</style>
