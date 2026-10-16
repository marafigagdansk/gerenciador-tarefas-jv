<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { ShieldAlert, KeyRound, LogOut } from 'lucide-vue-next'

const auth = useAuthStore()
const router = useRouter()

const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const erro = ref('')
const carregando = ref(false)

async function salvar() {
  erro.value = ''
  if (newPassword.value !== confirmPassword.value) {
    erro.value = 'A confirmação de senha não coincide com a nova senha.'
    return
  }
  if (newPassword.value.length < 6) {
    erro.value = 'A nova senha deve ter no mínimo 6 caracteres.'
    return
  }
  if (currentPassword.value === newPassword.value) {
    erro.value = 'A nova senha deve ser diferente da senha provisória.'
    return
  }

  carregando.value = true
  try {
    await auth.changePassword(currentPassword.value, newPassword.value)
    router.replace({ name: 'companies' })
  } catch (err) {
    erro.value = err.message
  } finally {
    carregando.value = false
  }
}

function sair() {
  auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <main class="auth-page">
    <form class="auth-card" @submit.prevent="salvar">
      <div class="auth-header">
        <div class="auth-badge">
          <ShieldAlert :size="20" class="badge-icon" />
          <span>Troca Obrigatória de Senha</span>
        </div>
        <h1>Defina sua nova senha</h1>
        <p class="subtitle">
          Olá<span v-if="auth.user?.name">, <strong>{{ auth.user.name }}</strong></span>! A senha informada pelo gestor é temporária e serve apenas para o primeiro acesso. Crie agora sua senha pessoal definitiva.
        </p>
      </div>

      <div v-if="erro" class="alert-error">{{ erro }}</div>

      <div class="form-group">
        <label for="current-password">Senha temporária atual</label>
        <input
          id="current-password"
          v-model="currentPassword"
          type="password"
          required
          autocomplete="current-password"
          placeholder="Senha recebida do master"
        />
      </div>

      <div class="form-group">
        <label for="new-password">Nova senha (mínimo 6 caracteres)</label>
        <input
          id="new-password"
          v-model="newPassword"
          type="password"
          required
          minlength="6"
          autocomplete="new-password"
          placeholder="Digite sua senha definitiva"
        />
      </div>

      <div class="form-group">
        <label for="confirm-password">Confirmar nova senha</label>
        <input
          id="confirm-password"
          v-model="confirmPassword"
          type="password"
          required
          minlength="6"
          autocomplete="new-password"
          placeholder="Repita a nova senha"
        />
      </div>

      <button id="btn-salvar-senha" type="submit" class="btn btn-primary" :disabled="carregando">
        <KeyRound :size="16" />
        {{ carregando ? 'Salvando nova senha...' : 'Salvar senha e continuar' }}
      </button>

      <div class="auth-footer-actions">
        <button type="button" class="btn-text" @click="sair">
          <LogOut :size="14" />
          Sair da conta
        </button>
      </div>
    </form>
  </main>
</template>

<style scoped>
.auth-header {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.auth-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.78rem;
  font-weight: 600;
  color: #B45309;
  background: #FFFBEB;
  border: 1px solid #FDE68A;
  border-radius: var(--radius-sm);
  padding: 0.25rem 0.65rem;
  width: fit-content;
}

.badge-icon {
  color: #B45309;
}

.auth-footer-actions {
  display: flex;
  justify-content: center;
  padding-top: 0.5rem;
  border-top: 1px solid var(--border-color);
}

.btn-text {
  background: transparent;
  border: none;
  color: var(--text-muted);
  font-size: 0.85rem;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  cursor: pointer;
  padding: 0.35rem 0.6rem;
  border-radius: var(--radius-sm);
  transition: color 0.15s, background 0.15s;
}

.btn-text:hover {
  color: var(--text-main);
  background: #F5F5F4;
}
</style>
