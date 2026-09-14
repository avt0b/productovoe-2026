import { http } from '@shared/utils/httpClient.js'

const BASE = '/api/search-hq'

export function listUpcomingTrips() {
  return http.get(`${BASE}/trips?upcoming_only=true`)
}

export function listSquads() {
  return http.get(`${BASE}/squads`)
}

export function registerForTrip(token, tripId) {
  return http.post(`${BASE}/trips/${tripId}/registrations`, undefined, { token })
}

export function cancelRegistration(token, tripId) {
  return http.delete(`${BASE}/trips/${tripId}/registrations/me`, { token })
}
