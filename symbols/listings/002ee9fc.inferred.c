/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

undefined4 FUN_002ee9fc(int param_1)

{
  undefined4 uVar1;
  
  pthread_mutex_lock((pthread_mutex_t *)(param_1 + 0xf8));
  if (*(int *)(param_1 + 0xf0) == param_1 + 0xf0) {
    uVar1 = 0;
  }
  else {
    uVar1 = *(undefined4 *)(*(int *)(param_1 + 0xf4) + 8);
  }
  pthread_mutex_unlock((pthread_mutex_t *)(param_1 + 0xf8));
  return uVar1;
}

