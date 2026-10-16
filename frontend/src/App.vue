<script setup>
import { RouterView, RouterLink, useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'

const auth = useAuthStore()
const router = useRouter()

function sair() {
  auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="app-root">
    <header class="navbar">
      <div class="navbar-container">
        <RouterLink :to="{ name: 'companies' }" class="brand">
          <span class="brand-icon">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
              <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-2 10H7v-2h10v2zm-4 4H7v-2h6v2zm4-8H7V7h10v2z" />
            </svg>
          </span>
          <span class="brand-title">Gerenciador de Tarefas</span>
        </RouterLink>

        <div v-if="auth.user" class="nav-user">
          <span class="user-name">{{ auth.user.name }}</span>
          <button id="btn-sair" class="btn btn-secondary btn-sm" @click="sair">Sair</button>
        </div>
      </div>
    </header>

    <RouterView />
  </div>
</template>

<style scoped>
.app-root {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.navbar {
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-card);
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.03);
  position: sticky;
  top: 0;
  z-index: 40;
}

.navbar-container {
  width: 100%;
  max-width: 100%;
  padding: 0.8rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: inherit;
  text-decoration: none;
}

.brand-icon {
  width: 32px;
  height: 32px;
  background: var(--primary);
  color: #fff;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
}

.brand-title {
  font-weight: 700;
  font-size: 1.1rem;
}

.nav-user {
  display: flex;
  align-items: center;
  gap: 0.9rem;
}

.user-name {
  font-size: 0.9rem;
  color: var(--text-muted);
}
</style>
