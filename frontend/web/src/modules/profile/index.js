export { default as routes } from './routes.js'
export { useProfileStore } from './profileStore.js'
// Низкоуровневый вызов api.js (не profileStore.js!) — у него нет своей
// зависимости от @modules/auth, поэтому его можно звать из auth/RegisterForm
// сразу после регистрации, не создавая цикл auth → profile → auth.
export { updateMyProfile } from './api.js'
