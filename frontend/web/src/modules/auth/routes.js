export default [
  {
    path: '/auth',
    name: 'auth-login',
    component: () => import('./AuthView.vue'),
    meta: { standalone: true },
  },
]
