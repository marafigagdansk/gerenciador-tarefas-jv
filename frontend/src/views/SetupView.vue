<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { maskDoc } from '../api'

const auth = useAuthStore()
const router = useRouter()

const form = ref({ name: '', email: '', password: '', company_name: '', cnpj: '' })
const erro = ref('')
const carregando = ref(false)

function onDoc(e) {
  form.value.cnpj = maskDoc(e.target.value)
}

async function salvar() {
  erro.value = ''
  carregando.value = true
  try {
    await auth.setup({ ...form.value })
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
    <form class="auth-card" @submit.prevent="salvar">
      <div>
        <h1>Configuração inicial</h1>
        <p class="subtitle">Crie o primeiro usuário (Master) e a primeira empresa.</p>
      </div>

      <div v-if="erro" class="alert-error">{{ erro }}</div>

      <div class="form-group">
        <label for="setup-name">Seu nome</label>
        <input id="setup-name" v-model="form.name" type="text" required autocomplete="name" />
      </div>
      <div class="form-group">
        <label for="setup-email">E-mail</label>
        <input id="setup-email" v-model="form.email" type="email" required autocomplete="email" />
      </div>
      <div class="form-group">
        <label for="setup-password">Senha (mín. 6 caracteres)</label>
        <input id="setup-password" v-model="form.password" type="password" required minlength="6" autocomplete="new-password" />
      </div>

      <h2>Primeira empresa</h2>

      <div class="form-group">
        <label for="setup-company">Nome da empresa</label>
        <input id="setup-company" v-model="form.company_name" type="text" required autocomplete="off" />
      </div>
      <div class="form-group">
        <label for="setup-cnpj">CNPJ (ou CPF)</label>
        <input id="setup-cnpj" :value="form.cnpj" @input="onDoc" type="text" required autocomplete="off" placeholder="00.000.000/0000-00" />
      </div>

      <button id="btn-setup" type="submit" class="btn btn-primary" :disabled="carregando">
        {{ carregando ? 'Criando...' : 'Criar conta e empresa' }}
      </button>
    </form>
  </main>
</template>
