<script setup>
import TaskWorkspace from '../components/TaskWorkspace.vue'
</script>

<template>
  <TaskWorkspace
    :project-id="null"
    kanban
    title="Tarefas Gerais"
    subtitle="Visíveis para todos os membros da empresa. Segure a alça de um card para reordenar ou mover entre colunas."
  />
</template>
