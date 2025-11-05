<template>
  <div class="pump-card-skeleton card">
    <div class="skeleton-header">
      <div class="skeleton skeleton-title"></div>
      <div class="skeleton skeleton-badge"></div>
    </div>
    <div class="skeleton-body">
      <div class="skeleton skeleton-text"></div>
      <div class="skeleton skeleton-text"></div>
    </div>
    <div class="skeleton-footer">
      <div class="skeleton skeleton-button"></div>
    </div>
  </div>
</template>

<style scoped>
.pump-card-skeleton {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 180px;
}

.skeleton-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.skeleton-title {
  height: 24px;
  flex: 1;
}

.skeleton-badge {
  height: 24px;
  width: 60px;
}

.skeleton-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.skeleton-text {
  height: 16px;
}

.skeleton-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: auto;
}

.skeleton-button {
  height: 36px;
  width: 120px;
}
</style>
