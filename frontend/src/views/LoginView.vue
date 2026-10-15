<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()

const email = ref('')
const password = ref('')
const erro = ref('')
const carregando = ref(false)

async function entrar() {
  erro.value = ''
  carregando.value = true
  try {
    await auth.login(email.value, password.value)
    router.push({ name: 'companies' })
  } catch (err) {
    erro.value = err.message
  } finally {
    carregando.value = false
  }
}
</script>

<template>
  <main class="auth-page">
    <form class="auth-card" @submit.prevent="entrar">
      <div>
        <h1>Entrar</h1>
        <p class="subtitle">Use seu e-mail e senha. Você escolhe a empresa na próxima tela.</p>
      </div>

      <div v-if="erro" class="alert-error">{{ erro }}</div>

      <div class="form-group">
        <label for="login-email">E-mail</label>
        <input id="login-email" v-model="email" type="email" required autocomplete="email" />
      </div>
      <div class="form-group">
        <label for="login-password">Senha</label>
        <input id="login-password" v-model="password" type="password" required autocomplete="current-password" />
      </div>

      <button id="btn-login" type="submit" class="btn btn-primary" :disabled="carregando">
        {{ carregando ? 'Entrando...' : 'Entrar' }}
      </button>
    </form>
  </main>
</template>
