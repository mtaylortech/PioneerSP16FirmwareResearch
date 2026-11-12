/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

/* WARNING: Unknown calling convention -- yet parameter storage is locked */
/* SUPPORTED ANALYST INTERPRETATION; address identity retained. Singleton construction, Message
   Thread and pthread_self. Original source signature is not recovered. */

MessageManager_view_0069826c * juce_get_message_manager_0069826c(void)

{
  int iVar1;
  undefined4 *puVar2;
  pthread_t pVar3;
  MessageManager_view_0069826c *pMVar4;
  undefined1 auStack_14 [4];
  
  iVar1 = DAT_006982f4;
  pMVar4 = *(MessageManager_view_0069826c **)(DAT_006982f4 + 4);
  if (pMVar4 == (MessageManager_view_0069826c *)0x0) {
    puVar2 = operator_new(0x28);
    *puVar2 = 0;
    *(undefined1 *)(puVar2 + 1) = 0;
    *(undefined1 *)((int)puVar2 + 5) = 0;
    pVar3 = pthread_self();
    puVar2[3] = 0;
    puVar2[2] = pVar3;
    FUN_00644ca8(puVar2 + 4);
    if (*(int *)(iVar1 + 0x3c) != 0) {
      FUN_0064a3fc(auStack_14,DAT_006982f8);
      FUN_00646f6c(auStack_14);
      FUN_00627f38(auStack_14);
    }
    *(undefined4 **)(iVar1 + 4) = puVar2;
    juce_x11_queue_bootstrap_00697fc0();
    pMVar4 = *(MessageManager_view_0069826c **)(iVar1 + 4);
  }
  return pMVar4;
}

