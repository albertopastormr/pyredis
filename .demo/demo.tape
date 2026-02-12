# Output configuration
Output demo.gif
Set FontSize 18
Set Width 1600
Set Height 800
Set Padding 40
Set FontFamily "JetBrains Mono"
Set Theme "Catppuccin Mocha"

# -----------------------------------------------------------------------------
# SETUP (Hidden)
# Check for tmux and cleanup old sessions
# -----------------------------------------------------------------------------
Hide
Type "tmux kill-session -t demo 2>/dev/null"
Enter
Type "reset"
Enter


# -----------------------------------------------------------------------------
# DEMO START
# -----------------------------------------------------------------------------

# 1. Start Tmux to show split screen
Type "tmux new-session -s demo"
Enter
Sleep 1s

# SETUP LEFT PANE PROMPT & HUD
Type "tmux set status off"
Enter
Type 'export PS1="pyredis $ "'
Enter
Type "clear"
Enter


# 2. Split the window horizontally 
# (Ctrl+B then %)
Ctrl+B
Type "%"
Sleep 1s

# SETUP RIGHT PANE PROMPT
Type 'export PS1="pyredis $ "'
Enter
Type "clear"
Enter

# 3. Setup Server Pane (Left)
# Switch to logging pane
Ctrl+B
Left
Sleep 500ms

Show
# Start the server (Visible) with DEBUG logs
Type "./run-redis.sh --debug"
Enter
Sleep 1s # Wait for "Ready to accept connections" log

# 4. Setup Client Pane (Right)
# Switch to client pane
Ctrl+B
Right
Sleep 500ms

# Start the interactive client
Type "python3 redis_client.py"
Enter
Sleep 1s
# Note: You should see "Client connected" log on the left pane now

# 5. Interaction
Type "PING"
Sleep 500ms
Enter
Sleep 1s

Type "SET mykey 'Hello World'"
Sleep 500ms
Enter
Sleep 1s

Type "GET mykey"
Sleep 500ms
Enter
Sleep 1s

Type "LPUSH demo_list item1 item2"
Sleep 500ms
Enter
Sleep 1s

Type "LRANGE demo_list 0 -1"
Sleep 500ms
Enter
Sleep 2s

# 6. Exit
Type "quit"
Sleep 500ms
Enter
Sleep 1s

# -----------------------------------------------------------------------------
# CLEANUP (Hidden)
# -----------------------------------------------------------------------------
Hide
# Kill the tmux session to clean up everything
Type "tmux kill-session -t demo"
Enter
