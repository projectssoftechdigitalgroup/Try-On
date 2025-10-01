const StatusIndicator = ({ isConnected }) => {
    return (
      <div className="flex items-center space-x-2">
        <div
          className={`w-3 h-3 rounded-full ${
            isConnected ? "bg-green-500" : "bg-red-500"
          } ${isConnected ? "animate-pulse" : ""}`}
        ></div>
        <span className="text-sm font-medium">{isConnected ? "Connected" : "Disconnected"}</span>
      </div>
    )
  }
  
  export default StatusIndicator
  