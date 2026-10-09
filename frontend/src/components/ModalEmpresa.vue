<script setup>
import { ref } from 'vue'

const props = defineProps({
  isOpen: Boolean
})

const emit = defineEmits(['close', 'created'])

const nome = ref('')
const documento = ref('')
const erro = ref('')
const carregando = ref(false)

function formatarDocumento(e) {
  let valor = e.target.value.replace(/\D/g, '')
  if (valor.length > 14) valor = valor.slice(0, 14)

  if (valor.length <= 11) {
    // CPF: 000.000.000-00
    valor = valor.replace(/(\d{3})(\d)/, '$1.$2')
    valor = valor.replace(/(\d{3})(\d)/, '$1.$2')
    valor = valor.replace(/(\d{3})(\d{1,2})$/, '$1-$2')
  } else {
    // CNPJ: 00.000.000/0000-00
    valor = valor.replace(/^(\d{2})(\d)/, '$1.$2')
    valor = valor.replace(/^(\d{2})\.(\d{3})(\d)/, '$1.$2.$3')
    valor = valor.replace(/\.(\d{3})(\d)/, '.$1/$2')
    valor = valor.replace(/(\d{4})(\d)/, '$1-$2')
  }
  documento.value = valor
}

async function salvar() {
  erro.value = ''
  const docLimpo = documento.value.replace(/\D/g, '')
  
  if (!nome.value.trim() || nome.value.trim().length < 2) {
    erro.value = 'O nome da empresa deve ter pelo menos 2 caracteres.'
    return
  }
  
  if (docLimpo.length !== 11 && docLimpo.length !== 14) {
    erro.value = 'Informe um CPF (11 dígitos) ou CNPJ (14 dígitos) válido.'
    return
  }

  carregando.value = true
  try {
    const res = await fetch('/api/empresas', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        nome: nome.value.trim(),
        documento: documento.value.trim()
      })
    })

    if (!res.ok) {
      const data = await res.json().catch(() => ({}))
      throw new Error(data.detail || 'Erro ao cadastrar empresa')
    }

    const novaEmpresa = await res.json()
    emit('created', novaEmpresa)
    fechar()
  } catch (err) {
    erro.value = err.message
  } finally {
    carregando.value = false
  }
}

function fechar() {
  nome.value = ''
  documento.value = ''
  erro.value = ''
  emit('close')
}
</script>

<template>
  <div v-if="isOpen" class="modal-backdrop" @click.self="fechar">
    <div class="modal-box">
      <div class="modal-header">
        <h3>Cadastrar Empresa</h3>
        <button class="btn-icon" @click="fechar" aria-label="Fechar">&times;</button>
      </div>

      <form @submit.prevent="salvar" class="modal-body">
        <div v-if="erro" class="alert-error">
          {{ erro }}
        </div>

        <div class="form-group">
          <label for="empresa-nome">Nome da Empresa</label>
          <input
            id="empresa-nome"
            v-model="nome"
            type="text"
            placeholder="Ex: Minha Empresa LTDA"
            required
            autocomplete="off"
          />
        </div>

        <div class="form-group">
          <label for="empresa-doc">CPF ou CNPJ</label>
          <input
            id="empresa-doc"
            :value="documento"
            @input="formatarDocumento"
            type="text"
            placeholder="000.000.000-00 ou 00.000.000/0000-00"
            required
            autocomplete="off"
          />
        </div>

        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="fechar" :disabled="carregando">
            Cancelar
          </button>
          <button type="submit" class="btn btn-primary" :disabled="carregando">
            {{ carregando ? 'Cadastrando...' : 'Cadastrar Empresa' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
  padding: 1rem;
  animation: fadeIn 0.15s ease-out;
}

.modal-box {
  background: #151d30;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-md);
  width: 100%;
  max-width: 460px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
  animation: scaleUp 0.15s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes scaleUp {
  from { transform: scale(0.96); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
  font-size: 1.15rem;
  font-weight: 600;
  color: #fff;
}

.btn-icon {
  background: transparent;
  border: none;
  color: var(--text-muted);
  font-size: 1.5rem;
  cursor: pointer;
  line-height: 1;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
}

.btn-icon:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.05);
}

.modal-body {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.form-group label {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--text-muted);
}

.form-group input {
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: var(--radius-sm);
  padding: 0.75rem 1rem;
  color: #fff;
  font-family: inherit;
  font-size: 0.95rem;
  outline: none;
  transition: border-color 0.15s ease;
}

.form-group input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 2px var(--primary-glow);
}

.alert-error {
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #fca5a5;
  padding: 0.65rem 0.85rem;
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 0.5rem;
}
</style>
