<script setup>
import { ref, computed, watch } from 'vue'
import { useCompanyStore } from '../stores/company'
import { X } from 'lucide-vue-next'

const props = defineProps({ isOpen: Boolean, projectId: { type: Number, default: null } })
const emit = defineEmits(['close'])

const company = useCompanyStore()
const selected = ref([])
const erro = ref('')
const carregando = ref(false)

const collaborators = computed(() =>
  company.members.filter((m) => m.role === 'collaborator' && m.is_active)
)

watch(() => props.isOpen, async (open) => {
  if (!open) return
  erro.value = ''
  try {
    selected.value = await company.getVisibility(props.projectId)
  } catch (err) {
    erro.value = err.message
  }
})

async function salvar() {
  erro.value = ''
  carregando.value = true
  try {
    await company.setVisibility(props.projectId, selected.value)
    emit('close')
  } catch (err) {
    erro.value = err.message
  } finally {
    carregando.value = false
  }
}
</script>

<template>
  <div v-if="isOpen" class="modal-backdrop" @click.self="emit('close')">
    <div class="modal-box">
      <div class="modal-header">
        <h3>Acesso ao Projeto</h3>
        <button class="btn-icon" @click="emit('close')" aria-label="Fechar">
          <X :size="20" />
        </button>
      </div>
      <form @submit.prevent="salvar" class="modal-body">
        <div v-if="erro" class="alert-error">{{ erro }}</div>
        <p class="hint">Colaboradores marcados enxergam este projeto e suas tarefas. Masters sempre têm acesso.</p>
        <div class="check-list">
          <label v-for="m in collaborators" :key="m.id" class="check-row">
            <input type="checkbox" :value="m.id" v-model="selected" />
            {{ m.name }}
          </label>
          <span v-if="collaborators.length === 0" class="hint">Nenhum colaborador cadastrado.</span>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="emit('close')">Cancelar</button>
          <button id="btn-salvar-acesso" type="submit" class="btn btn-primary" :disabled="carregando">Salvar acesso</button>
        </div>
      </form>
    </div>
  </div>
</template>
