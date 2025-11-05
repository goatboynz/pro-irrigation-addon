import { createRouter, createWebHashHistory } from 'vue-router'
import PumpsDashboard from '../views/PumpsDashboard.vue'
import ZoneManager from '../views/ZoneManager.vue'
import Settings from '../views/Settings.vue'

/**
 * Router configuration for Pro-Irrigation
 * Uses hash mode for compatibility with Home Assistant Ingress
 */
const routes = [
  {
    path: '/',
    name: 'dashboard',
    component: PumpsDashboard,
    meta: {
      title: 'Pumps Dashboard'
    }
  },
  {
    path: '/pump/:pumpId/zones',
    name: 'zone-manager',
    component: ZoneManager,
    meta: {
      title: 'Zone Manager'
    },
    props: true
  },
  {
    path: '/settings',
    name: 'settings',
    component: Settings,
    meta: {
      title: 'Global Settings'
    }
  },
  {
    // Catch-all redirect to dashboard
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  // Use hash mode for Ingress compatibility
  history: createWebHashHistory(),
  routes
})

// Navigation guard to update page title
router.beforeEach((to, from, next) => {
  // Update document title if meta.title is set
  if (to.meta.title) {
    document.title = `${to.meta.title} - Pro-Irrigation`
  }
  next()
})

export default router
