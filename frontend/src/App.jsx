import { useState, useEffect, useCallback } from 'react'
import './index.css'

// Use environment variable for API base or fallback to localhost
const API_BASE = import.meta.env.VITE_API_URL
const ADMIN_BASE = import.meta.env.VITE_ADMIN_URL 
const WS_BASE = import.meta.env.VITE_WS_URL 
const WS_URL = `${WS_BASE}/ws/orders/`

// Format Indonesian Rupiah
const formatRupiah = (amount) => {
  return `Rp ${Math.round(amount).toLocaleString('id-ID')}`
}

const STATUS_CONFIG = {
  pending: { label: 'Pending', color: 'bg-yellow-50 text-yellow-700 border-yellow-200', next: 'confirmed' },
  confirmed: { label: 'Confirmed', color: 'bg-blue-50 text-blue-700 border-blue-200', next: 'preparing' },
  preparing: { label: 'Preparing', color: 'bg-purple-50 text-purple-700 border-purple-200', next: 'ready' },
  ready: { label: 'Ready', color: 'bg-green-50 text-green-700 border-green-200', next: 'completed' },
  completed: { label: 'Completed', color: 'bg-gray-50 text-gray-600 border-gray-200', next: null },
  cancelled: { label: 'Cancelled', color: 'bg-red-50 text-red-700 border-red-200', next: null }
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
  const [currentTime, setCurrentTime] = useState(new Date())
  const [sidebarOpen, setSidebarOpen] = useState(false)

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 60000)
    return () => clearInterval(timer)
  }, [])

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
        showToast('Order status updated', 'success')
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
      }
      ws.onclose = () => {
        setWsConnected(false)
        reconnectTimeout = setTimeout(connect, 3000)
      }
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data)
        if (data.type === 'order_update') {
          if (data.data.action === 'new_order') {
            showToast(`New order #${data.data.order_number}`, 'success')
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

  const pendingOrders = orders.filter(o => o.status === 'pending').length

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile Overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-30 lg:hidden" 
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`fixed left-0 top-0 h-full w-64 bg-white border-r border-gray-200 z-40 transform transition-transform duration-300 ease-in-out ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0`}>
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="p-6 border-b border-gray-100 flex items-center justify-between">
            <div>
              <h1 className="text-xl font-semibold text-gray-900">BejoFood</h1>
              <p className="text-sm text-gray-500">Order Management</p>
            </div>
            {/* Close button for mobile */}
            <button 
              className="lg:hidden p-2 hover:bg-gray-100 rounded-lg text-gray-500"
              onClick={() => setSidebarOpen(false)}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-1">
            <NavItem label="Orders" active badge={pendingOrders > 0 ? pendingOrders : null} onClick={() => setSidebarOpen(false)} />
            <NavItem label="Menu" href={`${ADMIN_BASE}/admin/menu/menuitem/`} onClick={() => setSidebarOpen(false)} />
            <NavItem label="Customers" href={`${ADMIN_BASE}/admin/orders/telegramuser/`} onClick={() => setSidebarOpen(false)} />
            <NavItem label="Payments" href={`${ADMIN_BASE}/admin/payments/payment/`} onClick={() => setSidebarOpen(false)} />
            <NavItem label="Settings" href={`${ADMIN_BASE}/admin/`} onClick={() => setSidebarOpen(false)} />
          </nav>

          {/* Status */}
          <div className="p-4 border-t border-gray-100">
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <span className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-green-500' : 'bg-red-400'}`}></span>
              <span>{wsConnected ? 'Connected' : 'Offline'}</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="lg:ml-64 min-h-screen transition-all duration-300">
        <div className="p-4 sm:p-6 lg:p-8">
          {/* Mobile Header with Hamburger */}
          <div className="flex items-center gap-4 mb-6 lg:hidden">
            <button 
              onClick={() => setSidebarOpen(true)}
              className="p-2 hover:bg-gray-100 rounded-lg text-gray-600"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <div>
              <h1 className="text-lg font-semibold text-gray-900">BejoFood</h1>
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <span className={`w-1.5 h-1.5 rounded-full ${wsConnected ? 'bg-green-500' : 'bg-red-400'}`}></span>
                <span>{wsConnected ? 'Connected' : 'Offline'}</span>
              </div>
            </div>
          </div>

          {/* Telegram Bot Link */}
          <a
            href="https://t.me/BejoFoodBot"
            target="_blank"
            rel="noopener noreferrer"
            className="mb-6 lg:mb-8 block p-3 sm:p-4 bg-[#229ED9]/5 border border-[#229ED9]/20 rounded-xl hover:bg-[#229ED9]/10 transition-all flex items-center gap-3 sm:gap-4 group cursor-pointer"
          >
            <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-full bg-[#229ED9] text-white flex items-center justify-center shrink-0 shadow-lg shadow-[#229ED9]/20">
              <svg className="w-5 h-5 sm:w-6 sm:h-6 ml-[-2px] mt-[2px]" fill="currentColor" viewBox="0 0 24 24">
                <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.863.177-.176 3.293-3.018 3.355-3.268.007-.03.016-.241-.09-.344-.106-.102-.27-.068-.387-.042-.164.037-2.793 1.773-7.884 5.21-.4.276-.763.412-1.087.406-.598-.012-1.75-.337-2.607-.614-1.05-.337-1.879-.52-1.803-1.096.04-.3.42-.607 1.155-.923 4.542-1.975 7.574-3.277 9.097-3.91 4.318-1.8 5.212-2.112 5.795-2.114z"/>
              </svg>
            </div>
            <div className="min-w-0 flex-1">
              <div className="font-semibold text-gray-900 group-hover:text-[#229ED9] transition-colors text-sm sm:text-base truncate">Start Ordering w/ Telegram Bot</div>
              <div className="text-xs sm:text-sm text-gray-500 truncate">Click here to open the telegram bot</div>
            </div>
            <div className="hidden sm:block ml-auto text-[#229ED9] opacity-0 group-hover:opacity-100 transform translate-x-[-10px] group-hover:translate-x-0 transition-all shrink-0">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 8l4 4m0 0l-4 4m4-4H3"/>
              </svg>
            </div>
          </a>
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-6 lg:mb-8 gap-2">
            <div>
              <h1 className="text-xl sm:text-2xl font-semibold text-gray-900">Dashboard</h1>
              <p className="text-gray-500 text-xs sm:text-sm mt-1">
                {currentTime.toLocaleDateString('en-US', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}
              </p>
            </div>
          </div>

          {/* Stats Grid */}
          {stats && (
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 mb-6 lg:mb-8">
              <StatCard
                label="Today's Revenue"
                value={formatRupiah(stats.today?.revenue || 0)}
                subtext={`${stats.today?.orders || 0} orders`}
              />
              <StatCard
                label="Pending Orders"
                value={stats.pending_orders}
                subtext="Awaiting action"
                highlight={stats.pending_orders > 0}
              />
              <StatCard
                label="Today's Orders"
                value={stats.today?.orders || 0}
                subtext="Total orders"
              />
              <StatCard
                label="Total Customers"
                value={stats.total_customers}
                subtext="Registered"
              />
            </div>
          )}

          {/* Orders Section */}
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between px-4 sm:px-6 py-3 sm:py-4 border-b border-gray-100 gap-3">
              <div className="flex items-center gap-3">
                <h2 className="text-base sm:text-lg font-medium text-gray-900">Orders</h2>
                <span className="text-sm text-gray-500">({orders.length})</span>
              </div>
              <div className="flex gap-1 overflow-x-auto pb-1 sm:pb-0 -mx-1 px-1 scrollbar-hide">
                {FILTER_TABS.map(tab => (
                  <button
                    key={tab.value}
                    onClick={() => setFilter(tab.value)}
                    className={`px-2.5 sm:px-3 py-1.5 text-xs sm:text-sm font-medium rounded-md transition-colors whitespace-nowrap shrink-0 ${
                      filter === tab.value
                        ? 'bg-gray-900 text-white'
                        : 'text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Orders Table - Desktop */}
            <div className="hidden md:block overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-100">
                  <tr>
                    <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Order</th>
                    <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Customer</th>
                    <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Payment</th>
                    <th className="text-left px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Items</th>
                    <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Total</th>
                    <th className="text-right px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {loading ? (
                    <tr>
                      <td colSpan="7" className="px-6 py-12 text-center text-gray-500">
                        Loading orders...
                      </td>
                    </tr>
                  ) : orders.length === 0 ? (
                    <tr>
                      <td colSpan="7" className="px-6 py-12 text-center text-gray-500">
                        No orders found
                      </td>
                    </tr>
                  ) : (
                    orders.map(order => (
                      <tr 
                        key={order.id} 
                        className="hover:bg-gray-50 cursor-pointer"
                        onClick={() => setSelectedOrder(order)}
                      >
                        <td className="px-6 py-4">
                          <div className="font-medium text-gray-900">#{order.order_number}</div>
                          <div className="text-sm text-gray-500">{formatTime(order.created_at)}</div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="text-gray-900">{order.user?.first_name}</div>
                        </td>
                        <td className="px-6 py-4">
                          <span className={`inline-flex px-2.5 py-1 text-xs font-medium rounded-md border ${STATUS_CONFIG[order.status]?.color}`}>
                            {STATUS_CONFIG[order.status]?.label}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <span className={`inline-flex px-2.5 py-1 text-xs font-medium rounded-md border ${
                            order.payment_status === 'settlement' ? 'bg-green-50 text-green-700 border-green-200' :
                            order.payment_status === 'pending' ? 'bg-yellow-50 text-yellow-700 border-yellow-200' :
                            order.payment_status === 'expire' ? 'bg-red-50 text-red-700 border-red-200' :
                            'bg-gray-50 text-gray-600 border-gray-200'
                          }`}>
                            {order.payment_status === 'settlement' ? 'Paid' :
                             order.payment_status === 'pending' ? 'Pending' :
                             order.payment_status === 'expire' ? 'Expired' :
                             order.payment_status || 'N/A'}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-gray-600">
                          {order.item_count} items
                        </td>
                        <td className="px-6 py-4 text-right font-medium text-gray-900">
                          {formatRupiah(parseFloat(order.total))}
                        </td>
                        <td className="px-6 py-4 text-right">
                          {STATUS_CONFIG[order.status]?.next && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                updateOrderStatus(order.id, STATUS_CONFIG[order.status].next)
                              }}
                              className="px-3 py-1.5 text-sm font-medium text-white bg-gray-900 hover:bg-gray-700 active:bg-gray-800 rounded-md transition-all duration-150 cursor-pointer shadow-sm hover:shadow active:scale-95"
                            >
                              {STATUS_CONFIG[order.status].next === 'confirmed' ? 'Confirm' :
                               STATUS_CONFIG[order.status].next === 'preparing' ? 'Prepare' :
                               STATUS_CONFIG[order.status].next === 'ready' ? 'Ready' :
                               STATUS_CONFIG[order.status].next === 'completed' ? 'Complete' : 'Next'}
                            </button>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Orders Cards - Mobile */}
            <div className="md:hidden divide-y divide-gray-100">
              {loading ? (
                <div className="px-4 py-12 text-center text-gray-500">
                  Loading orders...
                </div>
              ) : orders.length === 0 ? (
                <div className="px-4 py-12 text-center text-gray-500">
                  No orders found
                </div>
              ) : (
                orders.map(order => (
                  <div 
                    key={order.id} 
                    className="p-4 hover:bg-gray-50 cursor-pointer active:bg-gray-100"
                    onClick={() => setSelectedOrder(order)}
                  >
                    {/* Order Header */}
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <div className="font-medium text-gray-900">#{order.order_number}</div>
                        <div className="text-sm text-gray-500">{order.user?.first_name} • {formatTime(order.created_at)}</div>
                      </div>
                      <div className="text-right">
                        <div className="font-semibold text-gray-900">{formatRupiah(parseFloat(order.total))}</div>
                        <div className="text-xs text-gray-500">{order.item_count} items</div>
                      </div>
                    </div>
                    
                    {/* Status Row */}
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className={`inline-flex px-2 py-0.5 text-xs font-medium rounded-md border ${STATUS_CONFIG[order.status]?.color}`}>
                          {STATUS_CONFIG[order.status]?.label}
                        </span>
                        <span className={`inline-flex px-2 py-0.5 text-xs font-medium rounded-md border ${
                          order.payment_status === 'settlement' ? 'bg-green-50 text-green-700 border-green-200' :
                          order.payment_status === 'pending' ? 'bg-yellow-50 text-yellow-700 border-yellow-200' :
                          order.payment_status === 'expire' ? 'bg-red-50 text-red-700 border-red-200' :
                          'bg-gray-50 text-gray-600 border-gray-200'
                        }`}>
                          {order.payment_status === 'settlement' ? 'Paid' :
                           order.payment_status === 'pending' ? 'Pending' :
                           order.payment_status === 'expire' ? 'Expired' :
                           order.payment_status || 'N/A'}
                        </span>
                      </div>
                      {STATUS_CONFIG[order.status]?.next && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            updateOrderStatus(order.id, STATUS_CONFIG[order.status].next)
                          }}
                          className="px-3 py-1.5 text-xs font-medium text-white bg-gray-900 hover:bg-gray-700 active:bg-gray-800 rounded-md transition-all duration-150 cursor-pointer"
                        >
                          {STATUS_CONFIG[order.status].next === 'confirmed' ? 'Confirm' :
                           STATUS_CONFIG[order.status].next === 'preparing' ? 'Prepare' :
                           STATUS_CONFIG[order.status].next === 'ready' ? 'Ready' :
                           STATUS_CONFIG[order.status].next === 'completed' ? 'Complete' : 'Next'}
                        </button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Footer */}
          <div className="mt-6 lg:mt-8 text-center text-xs sm:text-sm text-gray-400 pb-4">
            BejoFood Dashboard — Telegram Food Ordering System
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
      <div className="fixed bottom-6 right-6 z-50 space-y-2">
        {toasts.map(toast => (
          <div
            key={toast.id}
            className={`px-4 py-3 rounded-lg shadow-lg animate-slide-in ${
              toast.type === 'success' ? 'bg-green-600 text-white' :
              toast.type === 'error' ? 'bg-red-600 text-white' :
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

// Navigation Item
function NavItem({ label, active, href, badge, onClick }) {
  const className = `flex items-center justify-between px-4 py-2.5 rounded-lg text-sm font-medium transition-colors ${
    active ? 'bg-gray-100 text-gray-900' : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
  }`

  const content = (
    <>
      <span>{label}</span>
      {badge && (
        <span className="px-2 py-0.5 bg-red-500 text-white text-xs font-semibold rounded-full">{badge}</span>
      )}
    </>
  )

  if (href) {
    return <a href={href} target="_blank" rel="noopener noreferrer" className={className} onClick={onClick}>{content}</a>
  }

  return <div className={className} onClick={onClick}>{content}</div>
}

// Stat Card
function StatCard({ label, value, subtext, highlight }) {
  return (
    <div className={`bg-white rounded-lg border p-3 sm:p-5 ${highlight ? 'border-yellow-300' : 'border-gray-200'}`}>
      <div className="text-xs sm:text-sm text-gray-500 mb-0.5 sm:mb-1 truncate">{label}</div>
      <div className="text-lg sm:text-2xl font-semibold text-gray-900 truncate">{value}</div>
      <div className="text-xs sm:text-sm text-gray-400 mt-0.5 sm:mt-1 truncate">{subtext}</div>
    </div>
  )
}

// Order Modal
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

  const config = STATUS_CONFIG[order.status]

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-white rounded-xl w-full max-w-lg max-h-[90vh] overflow-hidden shadow-xl" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Order #{order.order_number}</h3>
            <p className="text-sm text-gray-500">{formatDate(order.created_at)} at {formatTime(order.created_at)}</p>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg text-gray-400 hover:text-gray-600">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-80px)]">
          {loading ? (
            <div className="text-center py-8 text-gray-500">Loading...</div>
          ) : detailedOrder && (
            <div className="space-y-6">
              {/* Status */}
              <div className="flex items-center gap-3">
                <span className={`flex-1 px-4 py-2.5 text-center text-sm font-medium rounded-lg border ${config?.color}`}>
                  {config?.label}
                </span>
                {config?.next && (
                  <button
                    onClick={() => onStatusChange(order.id, config.next)}
                    className="px-4 py-2.5 bg-gray-900 text-white text-sm font-medium rounded-lg hover:bg-gray-800 transition-colors"
                  >
                    Mark as {STATUS_CONFIG[config.next]?.label}
                  </button>
                )}
              </div>

              {/* Customer */}
              <div>
                <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Customer</label>
                <div className="text-gray-900">{detailedOrder.user?.first_name} {detailedOrder.user?.last_name}</div>
                <div className="text-sm text-gray-500">{detailedOrder.phone}</div>
              </div>

              {/* Address */}
              <div>
                <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Delivery Address</label>
                <div className="text-gray-700">{detailedOrder.delivery_address}</div>
              </div>

              {/* Notes */}
              {detailedOrder.notes && (
                <div>
                  <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Notes</label>
                  <div className="text-gray-700 italic">{detailedOrder.notes}</div>
                </div>
              )}

              {/* Items */}
              <div>
                <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Items</label>
                <div className="border border-gray-200 rounded-lg overflow-hidden">
                  <table className="w-full">
                    <tbody className="divide-y divide-gray-100">
                      {detailedOrder.items?.map((item, idx) => (
                        <tr key={idx}>
                          <td className="px-4 py-3">
                            <div className="font-medium text-gray-900">{item.name}</div>
                            <div className="text-sm text-gray-500">{formatRupiah(parseFloat(item.price))} × {item.quantity}</div>
                          </td>
                          <td className="px-4 py-3 text-right font-medium text-gray-900">
                            {formatRupiah(parseFloat(item.subtotal))}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-100">
                  <span className="text-gray-600 font-medium">Total</span>
                  <span className="text-xl font-semibold text-gray-900">{formatRupiah(parseFloat(detailedOrder.total))}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default App
