import { apiRequest } from './http'

export function getOrderHistory() {
  return apiRequest('/method/buy_in_minutes.buy_in_minutes.order_history.get_order_history')
}
