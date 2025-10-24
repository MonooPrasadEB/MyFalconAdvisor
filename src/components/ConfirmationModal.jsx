import { useState } from 'react'

export default function ConfirmationModal({ isOpen, onClose, onConfirm, title, message, action }) {
  const [isConfirming, setIsConfirming] = useState(false)

  if (!isOpen) return null

  const handleConfirm = async () => {
    setIsConfirming(true)
    try {
      await onConfirm()
      onClose()
    } catch (error) {
      console.error('Confirmation failed:', error)
    } finally {
      setIsConfirming(false)
    }
  }

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0,0,0,0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000
    }}>
      <div style={{
        backgroundColor: 'white',
        padding: 24,
        borderRadius: 8,
        maxWidth: 500,
        width: '90%',
        boxShadow: '0 4px 12px rgba(0,0,0,0.2)'
      }}>
        <h3 style={{ marginTop: 0 }}>{title}</h3>
        <p style={{ marginBottom: 24 }}>{message}</p>
        
        {action && (
          <div style={{
            backgroundColor: '#f5f5f5',
            padding: 12,
            borderRadius: 4,
            marginBottom: 24,
            fontFamily: 'monospace'
          }}>
            <strong>Action:</strong> {action}
          </div>
        )}
        
        <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end' }}>
          <button 
            onClick={onClose}
            disabled={isConfirming}
            style={{
              padding: '8px 16px',
              border: '1px solid #ddd',
              backgroundColor: 'white',
              borderRadius: 4,
              cursor: isConfirming ? 'not-allowed' : 'pointer'
            }}
          >
            Cancel
          </button>
          <button 
            onClick={handleConfirm}
            disabled={isConfirming}
            style={{
              padding: '8px 16px',
              border: 'none',
              backgroundColor: '#007bff',
              color: 'white',
              borderRadius: 4,
              cursor: isConfirming ? 'not-allowed' : 'pointer'
            }}
          >
            {isConfirming ? 'Confirming...' : 'Confirm'}
          </button>
        </div>
      </div>
    </div>
  )
}
