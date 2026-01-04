import { useState, useEffect, useCallback } from 'react'
import './index.css'

const API_BASE = 'http://localhost:8000/api/v1'
const WS_URL = 'ws://localhost:8000/ws/orders/'

// Format Indonesian Rupiah
const formatRupiah = (amount) => {
  return `Rp ${Math.round(amount).toLocaleString('id-ID')}`
}

const STATUS_CONFIG = {
  pending: { label: 'Pending', color: 'bg-amber-100 text-amber-700', icon: '⏳' },
  confirmed: { label: 'Confirmed', color: 'bg-blue-100 text-blue-700', icon: '✓' },
  preparing: { label: 'Preparing', color: 'bg-purple-100 text-purple-700', icon: '👨‍🍳' },
  ready: { label: 'Ready', color: 'bg-green-100 text-green-700', icon: '🎉' },
  completed: { label: 'Completed', color: 'bg-gray-100 text-gray-600', icon: '✔' },
  cancelled: { label: 'Cancelled', color: 'bg-red-100 text-red-700', icon: '✕' }
}

const FILTER_TABS = [
  { value: '', label: 'All Orders' },
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

  const showToast = useCallback((message, type = 'info') => {
    const id = Date.now()
    setToasts(prev => [...prev, { id, message, type }])
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 4000)
  }, [])

  const fetchOrders = useCallback(async () => {
    try {
      const url = filter ? `${API_BASE}/orders/?status=${filter}` : `${API_BASE}/orders/`
      const res = await fetch(url)
      const data = await res.json()
      setOrders(data.results || data)
    } catch (err) {
      console.error('Failed to fetch orders:', err)
    } finally {
      setLoading(false)
    }
  }, [filter])

  const fetchStats = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/stats/`)
      const data = await res.json()
      setStats(data)
    } catch (err) {
      console.error('Failed to fetch stats:', err)
    }
  }, [])

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
        reconnectTimeout = setTimeout(connect, 3000)
      }
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data)
        if (data.type === 'order_update') {
          if (data.data.action === 'new_order') {
            showToast(`New order #${data.data.order_number}!`, 'success')
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

  useEffect(() => {
    fetchOrders()
    fetchStats()
  }, [fetchOrders, fetchStats])

  const formatTime = (dateString) => {
    return new Date(dateString).toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' })
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' })
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="fixed left-0 top-0 h-full w-64 bg-white border-r border-gray-200 z-40">
        <div className="p-6">
          <div className="flex items-center gap-3 mb-8">
            <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl flex items-center justify-center text-white text-xl">
              🍔
            </div>
            <span className="text-xl font-bold bg-gradient-to-r from-primary-500 to-primary-600 bg-clip-text text-transparent">
              BejoFood
            </span>
          </div>

          <nav className="space-y-1">
            <a className="flex items-center gap-3 px-4 py-3 rounded-lg bg-primary-50 text-primary-600 font-medium cursor-pointer">
              <span>📦</span>
              <span>Orders</span>
            </a>
            <a href="http://localhost:8000/admin/menu/menuitem/" target="_blank" rel="noopener noreferrer"
              className="flex items-center gap-3 px-4 py-3 rounded-lg text-gray-600 hover:bg-gray-50 transition-colors cursor-pointer">
              <span>🍽️</span>
              <span>Menu</span>
            </a>
            <a href="http://localhost:8000/admin/" target="_blank" rel="noopener noreferrer"
              className="flex items-center gap-3 px-4 py-3 rounded-lg text-gray-600 hover:bg-gray-50 transition-colors cursor-pointer">
              <span>⚙️</span>
              <span>Settings</span>
            </a>
          </nav>
        </div>

        <div className="absolute bottom-0 left-0 right-0 p-6 border-t border-gray-100">
          <div className="flex items-center gap-2 text-sm">
            <span className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-green-500' : 'bg-red-400'}`}></span>
            <span className="text-gray-500">{wsConnected ? 'Live updates' : 'Offline'}</span>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="ml-64 min-h-screen">
        <div className="p-8">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
            <p className="text-gray-500">Manage your food orders</p>
          </div>

          {/* Stats Grid */}
          {stats && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <StatCard
                icon="📦"
                iconBg="bg-amber-100"
                label="Pending Orders"
                value={stats.pending_orders}
              />
              <StatCard
                icon="💰"
                iconBg="bg-green-100"
                label="Today's Revenue"
                value={formatRupiah(stats.today?.revenue || 0)}
              />
              <StatCard
                icon="📋"
                iconBg="bg-blue-100"
                label="Today's Orders"
                value={stats.today?.orders || 0}
              />
              <StatCard
                icon="👥"
                iconBg="bg-purple-100"
                label="Total Customers"
                value={stats.total_customers}
              />
            </div>
          )}

          {/* Orders Section */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            {/* Filter Tabs */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
              <h2 className="text-lg font-semibold text-gray-900">Orders</h2>
              <div className="flex gap-2">
                {FILTER_TABS.map(tab => (
                  <button
                    key={tab.value}
                    onClick={() => setFilter(tab.value)}
                    className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                      filter === tab.value
                        ? 'bg-primary-500 text-white'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Orders List */}
            <div className="divide-y divide-gray-100 max-h-[calc(100vh-400px)] overflow-y-auto">
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <div className="w-8 h-8 border-4 border-primary-200 border-t-primary-500 rounded-full animate-spin"></div>
                </div>
              ) : orders.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <div className="text-4xl mb-2">📭</div>
                  <p>No orders found</p>
                </div>
              ) : (
                orders.map(order => (
                  <div
                    key={order.id}
                    onClick={() => setSelectedOrder(order)}
                    className="px-6 py-4 hover:bg-gray-50 cursor-pointer transition-colors"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <span className="font-semibold text-gray-900">#{order.order_number}</span>
                        <span className="text-sm text-gray-400">{formatTime(order.created_at)}</span>
                      </div>
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${STATUS_CONFIG[order.status]?.color}`}>
                        {STATUS_CONFIG[order.status]?.icon} {STATUS_CONFIG[order.status]?.label}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 text-sm text-gray-500">
                        <span>👤</span>
                        <span>{order.user?.first_name} {order.user?.last_name}</span>
                      </div>
                      <div className="flex items-center gap-4">
                        <span className="text-sm text-gray-500">{order.item_count} items</span>
                        <span className="font-semibold text-primary-600">{formatRupiah(parseFloat(order.total))}</span>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </main>

      {/* Order Modal */}
      {selectedOrder && (
        <OrderModal
          order={selectedOrder}
          onClose={() => setSelectedOrder(null)}
          onStatusChange={updateOrderStatus}
          formatDate={formatDate}
          formatTime={formatTime}
        />
      )}

      {/* Toasts */}
      <div className="fixed bottom-6 right-6 z-50 space-y-3">
        {toasts.map(toast => (
          <div
            key={toast.id}
            className={`px-4 py-3 rounded-lg shadow-lg animate-slide-in flex items-center gap-2 ${
              toast.type === 'success' ? 'bg-green-500 text-white' :
              toast.type === 'error' ? 'bg-red-500 text-white' :
              'bg-gray-800 text-white'
            }`}
          >
            {toast.message}
          </div>
        ))}
      </div>
    </div>
  )
}

// Stat Card Component
function StatCard({ icon, iconBg, label, value }) {
  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
      <div className={`w-12 h-12 ${iconBg} rounded-xl flex items-center justify-center text-2xl mb-4`}>
        {icon}
      </div>
      <div className="text-2xl font-bold text-gray-900 mb-1">{value}</div>
      <div className="text-sm text-gray-500">{label}</div>
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

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl w-full max-w-lg max-h-[90vh] overflow-hidden" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h3 className="text-lg font-semibold text-gray-900">Order #{order.order_number}</h3>
          <button onClick={onClose} className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-600">
            ✕
          </button>
        </div>

        {/* Body */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-80px)]">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="w-8 h-8 border-4 border-primary-200 border-t-primary-500 rounded-full animate-spin"></div>
            </div>
          ) : detailedOrder && (
            <div className="space-y-6">
              {/* Status */}
              <div>
                <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Status</label>
                <select
                  value={detailedOrder.status}
                  onChange={(e) => onStatusChange(order.id, e.target.value)}
                  className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
                >
                  {Object.entries(STATUS_CONFIG).map(([value, config]) => (
                    <option key={value} value={value}>{config.icon} {config.label}</option>
                  ))}
                </select>
              </div>

              {/* Customer */}
              <div>
                <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Customer</label>
                <p className="font-medium text-gray-900">{detailedOrder.user?.first_name} {detailedOrder.user?.last_name}</p>
                <p className="text-sm text-gray-500">📞 {detailedOrder.phone}</p>
              </div>

              {/* Address */}
              <div>
                <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Delivery Address</label>
                <p className="text-gray-700">{detailedOrder.delivery_address}</p>
              </div>

              {/* Notes */}
              {detailedOrder.notes && (
                <div>
                  <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Notes</label>
                  <p className="text-gray-700 italic">{detailedOrder.notes}</p>
                </div>
              )}

              {/* Items */}
              <div>
                <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Items</label>
                <div className="bg-gray-50 rounded-lg overflow-hidden">
                  <table className="w-full">
                    <thead>
                      <tr className="text-xs text-gray-500 uppercase">
                        <th className="text-left px-4 py-2 font-medium">Item</th>
                        <th className="text-center px-4 py-2 font-medium">Qty</th>
                        <th className="text-right px-4 py-2 font-medium">Price</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {detailedOrder.items?.map((item, idx) => (
                        <tr key={idx} className="text-sm">
                          <td className="px-4 py-3 font-medium text-gray-900">{item.name}</td>
                          <td className="px-4 py-3 text-center text-gray-600">{item.quantity}</td>
                          <td className="px-4 py-3 text-right text-gray-900">{formatRupiah(parseFloat(item.subtotal))}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-200">
                  <span className="font-medium text-gray-600">Total</span>
                  <span className="text-xl font-bold text-primary-600">{formatRupiah(parseFloat(detailedOrder.total))}</span>
                </div>
              </div>

              {/* Time */}
              <div className="text-sm text-gray-500">
                Ordered on {formatDate(detailedOrder.created_at)} at {formatTime(detailedOrder.created_at)}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default App
