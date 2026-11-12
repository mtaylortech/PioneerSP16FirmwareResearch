/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

/* SUPPORTED ANALYST INTERPRETATION; address identity retained. vtable +0x30 call, return at
   000b4060, nonzero branch to dispatch call 000b4094. Original source signature is not recovered.
    */

int main_initialise_then_dispatch_000b4034(void)

{
  int *piVar1;
  int iVar2;
  MessageManager_view_0069826c *manager;
  undefined1 auStack_14 [8];
  
  FUN_00698468(auStack_14);
  piVar1 = (int *)(**(code **)(DAT_000b40c8 + 0x3c))();
  iVar2 = (**(code **)(*piVar1 + 0x30))();
  if (iVar2 == 0) {
    iVar2 = piVar1[1];
  }
  else {
    manager = juce_get_message_manager_0069826c();
    juce_x11_message_dispatch_0069afc0(manager);
    iVar2 = FUN_00698384(piVar1);
  }
  (**(code **)(*piVar1 + 4))(piVar1);
  FUN_0069a9e8(auStack_14);
  return iVar2;
}

