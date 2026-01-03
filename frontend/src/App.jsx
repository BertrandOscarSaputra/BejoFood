import { useState, useEffect, useCallback } from 'react'
import './index.css'

const API_BASE = 'http://localhost:8000/api/v1'
const WS_URL = 'ws://localhost:8000/ws/orders/'

// Status configurations
const STATUS_CONFIG = {
  pending: { label: 'Pending', icon: '⏳' },
  confirmed: { label: 'Confirmed', icon: '✅' },
  preparing: { label: 'Preparing', icon: '👨‍🍳' },
  ready: { label: 'Ready', icon: '🎉' },
  completed: { label: 'Completed', icon: '✔️' },
  cancelled: { label: 'Cancelled', icon: '❌' }
}

const FILTER_TABS = [
  { value: '', label: 'All' },
  { value: 'pending', label: 'Pending' },
  { value: 'preparing', label: 'Preparing' },
  { value: 'ready', label: 'Ready' },
  { value: 'completed', label: 'Completed' }
]

function App() {
  const [orders, setOrders] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('')
  const [selectedOrder, setSelectedOrder] = useState(null)
  const [wsConnected, setWsConnected] = useState(false)
  const [toasts, setToasts] = useState([])

  // Show toast notification
  const showToast = useCallback((message, type = 'info') => {
    const id = Date.now()
    setToasts(prev => [...prev, { id, message, type }])
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id))
    }, 4000)
  }, [])

  // Fetch orders
  const fetchOrders = useCallback(async () => {
    try {
      const url = filter 
        ? `${API_BASE}/orders/?status=${filter}`
        : `${API_BASE}/orders/`
      const res = await fetch(url)
      const data = await res.json()
      setOrders(data.results || data)
    } catch (err) {
      console.error('Failed to fetch orders:', err)
    } finally {
      setLoading(false)
    }
  }, [filter])

  // Fetch stats
  const fetchStats = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/stats/`)
      const data = await res.json()
      setStats(data)
    } catch (err) {
      console.error('Failed to fetch stats:', err)
    }
  }, [])

  // Update order status
  const updateOrderStatus = async (orderId, newStatus) => {
    try {
      const res = await fetch(`${API_BASE}/orders/${orderId}/update_status/`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus })
      })
      
      if (res.ok) {
        showToast('Order status updated!', 'success')
        fetchOrders()
        fetchStats()
        if (selectedOrder?.id === orderId) {
          setSelectedOrder(prev => ({ ...prev, status: newStatus }))
        }
      }
    } catch {
      showToast('Failed to update status', 'error')
    }
  }

  // WebSocket connection
  useEffect(() => {
    let ws = null
    let reconnectTimeout = null

    const connect = () => {
      ws = new WebSocket(WS_URL)
      
      ws.onopen = () => {
        setWsConnected(true)
        console.log('WebSocket connected')
      }
      
      ws.onclose = () => {
        setWsConnected(false)
        console.log('WebSocket disconnected, reconnecting...')
        reconnectTimeout = setTimeout(connect, 3000)
      }
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data)
        console.log('WS message:', data)
        
        if (data.type === 'order_update') {
          if (data.data.action === 'new_order') {
            showToast(`New order #${data.data.order_number}!`, 'success')
            // Play notification sound
            playNotificationSound()
          }
          fetchOrders()
          fetchStats()
        }
      }
    }

    connect()

    return () => {
      if (ws) ws.close()
      if (reconnectTimeout) clearTimeout(reconnectTimeout)
    }
  }, [fetchOrders, fetchStats, showToast])

  // Initial fetch
  useEffect(() => {
    fetchOrders()
    fetchStats()
  }, [fetchOrders, fetchStats])

  // Play notification sound
  const playNotificationSound = () => {
    const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2teleR8pXrHz36BzGBVPsuvktH8jEkC69e+1fB8MN7v2+7qAIA45v/r9vn4gBjG9/P/AfyABLr79AMA8IBYxxf8Bwn4gACy//wHDfR8ALcD/AcR9HwAtv/8BxH0fAC3A/wDEfB8ALcD/AMR9HwAtwP8AxH0fAC3A/wHEfR8ALcD/AcR9HwAuwP8Bw30fAC7B/wHDfR8AL8L/AcJ9HwAww/8BwX0fADHE/wHBfR8AMcX/AcB9HwAyxv8Bv30fADPH/wG/fR8AM8j/Ab59HwA0yf8Bvn0fADXK/wG9fR8ANcv/Abx9HwA2zP8BvH0f')
    audio.play().catch(() => {}) // Ignore errors
  }

  // Format time
  const formatTime = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: true 
    })
  }

  // Format date
  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      year: 'numeric'
    })
  }

  return (
    <div className="app">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="logo">
          <span>🍔</span>
          <span>BejoFood</span>
        </div>
        
        <nav>
          <ul className="nav-menu">
            <li className="nav-item">
              <a className="nav-link active">
                <span>📦</span>
                <span>Orders</span>
              </a>
            </li>
            <li className="nav-item">
              <a className="nav-link" href="/admin/menu/menuitem/" target="_blank">
                <span>🍽️</span>
                <span>Menu</span>
              </a>
            </li>
            <li className="nav-item">
              <a className="nav-link" href="/admin/" target="_blank">
                <span>⚙️</span>
                <span>Settings</span>
              </a>
            </li>
          </ul>
        </nav>

        <div style={{ marginTop: 'auto', paddingTop: '2rem' }}>
          <div className="connection-status">
            <span className={`connection-dot ${wsConnected ? 'connected' : 'disconnected'}`}></span>
            <span>{wsConnected ? 'Live' : 'Offline'}</span>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        {/* Header */}
        <header className="header">
          <h1>
            <span>📊</span>
            Dashboard
          </h1>
        </header>

        {/* Stats */}
        {stats && (
          <div className="stats-grid">
            <div className="stat-card">
              <div className="icon primary">📦</div>
              <div className="value">{stats.pending_orders}</div>
              <div className="label">Pending Orders</div>
            </div>
            <div className="stat-card">
              <div className="icon success">💰</div>
              <div className="value">Rp{stats.today?.revenue?.toLocaleString() || 0}</div>
              <div className="label">Today's Revenue</div>
            </div>
            <div className="stat-card">
              <div className="icon warning">📋</div>
              <div className="value">{stats.today?.orders || 0}</div>
              <div className="label">Today's Orders</div>
            </div>
            <div className="stat-card">
              <div className="icon info">👥</div>
              <div className="value">{stats.total_customers}</div>
              <div className="label">Total Customers</div>
            </div>
          </div>
        )}

        {/* Orders Section */}
        <section className="orders-section">
          <div className="orders-header">
            <h2>
              <span>📦</span>
              Orders
            </h2>
            <div className="filter-tabs">
              {FILTER_TABS.map(tab => (
                <button
                  key={tab.value}
                  className={`filter-tab ${filter === tab.value ? 'active' : ''}`}
                  onClick={() => setFilter(tab.value)}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          <div className="orders-list">
            {loading ? (
              <div className="loading-spinner">
                <div className="spinner"></div>
              </div>
            ) : orders.length === 0 ? (
              <div className="empty-state">
                <div className="icon">📭</div>
                <p>No orders found</p>
              </div>
            ) : (
              orders.map(order => (
                <div 
                  key={order.id} 
                  className="order-card"
                  onClick={() => setSelectedOrder(order)}
                >
                  <div className="order-header">
                    <div>
                      <span className="order-number">#{order.order_number}</span>
                      <span className="order-time"> • {formatTime(order.created_at)}</span>
                    </div>
                    <span className={`status-badge ${order.status}`}>
                      {STATUS_CONFIG[order.status]?.icon} {STATUS_CONFIG[order.status]?.label}
                    </span>
                  </div>
                  <div className="order-customer">
                    <span>👤</span>
                    <span>{order.user?.first_name} {order.user?.last_name}</span>
                  </div>
                  <div className="order-details">
                    <span className="order-items">{order.item_count} items</span>
                    <span className="order-total">Rp{parseFloat(order.total).toLocaleString()}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </section>
      </main>

      {/* Order Detail Modal */}
      {selectedOrder && (
        <OrderModal 
          order={selectedOrder}
          onClose={() => setSelectedOrder(null)}
          onStatusChange={updateOrderStatus}
          formatDate={formatDate}
          formatTime={formatTime}
        />
      )}

      {/* Toast Container */}
      <div className="toast-container">
        {toasts.map(toast => (
          <div key={toast.id} className={`toast ${toast.type}`}>
            {toast.message}
          </div>
        ))}
      </div>
    </div>
  )
}

// Order Modal Component
function OrderModal({ order, onClose, onStatusChange, formatDate, formatTime }) {
  const [detailedOrder, setDetailedOrder] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchDetails = async () => {
      try {
        const res = await fetch(`${API_BASE}/orders/${order.id}/`)
        const data = await res.json()
        setDetailedOrder(data)
      } catch (err) {
        console.error('Failed to fetch order details:', err)
      } finally {
        setLoading(false)
      }
    }
    fetchDetails()
  }, [order.id])

  const handleStatusChange = (e) => {
    onStatusChange(order.id, e.target.value)
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Order #{order.order_number}</h3>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        <div className="modal-body">
          {loading ? (
            <div className="loading-spinner">
              <div className="spinner"></div>
            </div>
          ) : detailedOrder && (
            <>
              {/* Status Update */}
              <div className="modal-section">
                <h4>Status</h4>
                <div className="status-dropdown">
                  <select value={detailedOrder.status} onChange={handleStatusChange}>
                    {Object.entries(STATUS_CONFIG).map(([value, config]) => (
                      <option key={value} value={value}>
                        {config.icon} {config.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Customer Info */}
              <div className="modal-section">
                <h4>Customer</h4>
                <p><strong>{detailedOrder.user?.first_name} {detailedOrder.user?.last_name}</strong></p>
                {detailedOrder.user?.username && <p>@{detailedOrder.user?.username}</p>}
                <p>📞 {detailedOrder.phone}</p>
              </div>

              {/* Delivery Address */}
              <div className="modal-section">
                <h4>Delivery Address</h4>
                <p>{detailedOrder.delivery_address}</p>
              </div>

              {/* Notes */}
              {detailedOrder.notes && (
                <div className="modal-section">
                  <h4>Notes</h4>
                  <p>{detailedOrder.notes}</p>
                </div>
              )}

              {/* Order Items */}
              <div className="modal-section">
                <h4>Items</h4>
                <table className="order-items-table">
                  <thead>
                    <tr>
                      <th>Item</th>
                      <th>Qty</th>
                      <th>Price</th>
                      <th className="subtotal">Subtotal</th>
                    </tr>
                  </thead>
                  <tbody>
                    {detailedOrder.items?.map((item, idx) => (
                      <tr key={idx}>
                        <td className="item-name">{item.name}</td>
                        <td>{item.quantity}</td>
                        <td>Rp{parseFloat(item.price).toLocaleString()}</td>
                        <td className="subtotal">Rp{parseFloat(item.subtotal).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                <div className="order-total-row">
                  <span className="label">Total</span>
                  <span className="value">Rp{parseFloat(detailedOrder.total).toLocaleString()}</span>
                </div>
              </div>

              {/* Timestamps */}
              <div className="modal-section">
                <h4>Order Time</h4>
                <p>{formatDate(detailedOrder.created_at)} at {formatTime(detailedOrder.created_at)}</p>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default App
