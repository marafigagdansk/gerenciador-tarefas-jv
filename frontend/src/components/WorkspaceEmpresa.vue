<script setup>
const props = defineProps({
  empresa: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['back'])
</script>

<template>
  <div class="workspace-container">
    <header class="workspace-header">
      <div class="header-left">
        <button class="btn btn-secondary btn-voltar" @click="emit('back')">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
            <line x1="19" y1="12" x2="5" y2="12"></line>
            <polyline points="12 19 5 12 12 5"></polyline>
          </svg>
          Voltar às empresas
        </button>

        <div class="empresa-info">
          <h2>{{ empresa.nome }}</h2>
          <span class="doc-tag">{{ empresa.documento }}</span>
        </div>
      </div>
    </header>

    <main class="workspace-content">
      <div class="empty-state">
        <div class="empty-icon">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="48" height="48">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
            <line x1="9" y1="9" x2="15" y2="9"></line>
            <line x1="9" y1="13" x2="15" y2="13"></line>
            <line x1="9" y1="17" x2="11" y2="17"></line>
          </svg>
        </div>
        <h3>Área da Empresa</h3>
        <p>O conteúdo e gerenciamento de tarefas desta empresa serão adicionados no próximo passo.</p>
      </div>
    </main>
  </div>
</template>

<style scoped>
.workspace-container {
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - 80px);
}

.workspace-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 0;
  border-bottom: 1px solid var(--border-color);
  margin-bottom: 2rem;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.btn-voltar {
  padding: 0.5rem 0.9rem;
  font-size: 0.85rem;
}

.empresa-info h2 {
  font-size: 1.4rem;
  font-weight: 700;
  color: #fff;
}

.doc-tag {
  font-size: 0.8rem;
  color: var(--text-muted);
}

.workspace-content {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-state {
  text-align: center;
  padding: 3rem 2rem;
  background: var(--bg-card);
  border: 1px dashed rgba(255, 255, 255, 0.15);
  border-radius: var(--radius-lg);
  max-width: 500px;
  width: 100%;
}

.empty-icon {
  color: var(--text-subtle);
  margin-bottom: 1rem;
  display: flex;
  justify-content: center;
}

.empty-state h3 {
  font-size: 1.2rem;
  font-weight: 600;
  color: #fff;
  margin-bottom: 0.5rem;
}

.empty-state p {
  font-size: 0.9rem;
  color: var(--text-muted);
  line-height: 1.5;
}
</style>
