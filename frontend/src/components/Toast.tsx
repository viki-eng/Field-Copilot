import { useEffect } from 'react'
import { CheckCircle } from 'lucide-react'

interface ToastProps {
  message: string
  onDismiss: () => void
}

export function Toast({ message, onDismiss }: ToastProps) {
  useEffect(() => {
    const t = setTimeout(onDismiss, 3500)
    return () => clearTimeout(t)
  }, [message, onDismiss])

  return (
    <div style={{
      position: 'fixed', bottom: 24, right: 24,
      background: '#0f172a', color: '#f8fafc',
      padding: '12px 18px', borderRadius: 10,
      fontSize: 13, fontWeight: 500,
      boxShadow: '0 10px 15px rgba(0,0,0,0.15), 0 4px 6px rgba(0,0,0,0.1)',
      zIndex: 9999, display: 'flex', alignItems: 'center', gap: 10,
      animation: 'toastIn 0.3s cubic-bezier(0.16,1,0.3,1)',
      maxWidth: 360,
    }}>
      <style>{`@keyframes toastIn { from { opacity:0; transform:translateY(12px) scale(0.95); } to { opacity:1; transform:translateY(0) scale(1); } }`}</style>
      <CheckCircle size={16} color="#4ade80" style={{ flexShrink: 0 }} />
      {message}
    </div>
  )
}
