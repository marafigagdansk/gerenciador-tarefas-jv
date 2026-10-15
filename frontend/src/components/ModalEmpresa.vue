<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'
import { maskDoc } from '../api'
import { X } from 'lucide-vue-next'

defineProps({ isOpen: Boolean })
const emit = defineEmits(['close'])

const auth = useAuthStore()
const name = ref('')
const cnpj = ref('')
const erro = ref('')
const carregando = ref(false)

function onDoc(e) {
  cnpj.value = maskDoc(e.target.value)
}

async function salvar() {
  erro.value = ''
  carregando.value = true
  try {
    await auth.createCompany({ name: name.value, cnpj: cnpj.value })
    fechar()
  } catch (err) {
    erro.value = err.message
  } finally {
    carregando.value = false
  }
}

function fechar() {
  name.value = ''
  cnpj.value = ''
  erro.value = ''
  emit('close')
}
</script>

<template>
  <div v-if="isOpen" class="modal-backdrop" @click.self="fechar">
    <div class="modal-box">
      <div class="modal-header">
        <h3>Nova Empresa</h3>
        <button class="btn-icon" @click="fechar" aria-label="Fechar">
          <X :size="20" />
        </button>
      </div>
      <form @submit.prevent="salvar" class="modal-body">
        <div v-if="erro" class="alert-error">{{ erro }}</div>
        <div class="form-group">
          <label for="empresa-nome">Nome da empresa</label>
          <input id="empresa-nome" v-model="name" type="text" required autocomplete="off" />
        </div>
        <div class="form-group">
          <label for="empresa-doc">CNPJ (ou CPF)</label>
          <input id="empresa-doc" :value="cnpj" @input="onDoc" type="text" required autocomplete="off" placeholder="00.000.000/0000-00" />
        </div>
        <p class="hint">Você será Master desta empresa.</p>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="fechar" :disabled="carregando">Cancelar</button>
          <button id="btn-salvar-empresa" type="submit" class="btn btn-primary" :disabled="carregando">
            {{ carregando ? 'Criando...' : 'Criar empresa' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
