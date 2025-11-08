export default function StatusIndicator({ isConnected }) {
  return (
    <div className="status-indicator">
      <div className={`status-badge ${isConnected ? "connected" : "disconnected"}`}>
        <span className="status-dot"></span>
        <span className="status-text">{isConnected ? "Connected" : "Disconnected"}</span>
      </div>
    </div>
  )
}
