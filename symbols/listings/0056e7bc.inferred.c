/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

/* WARNING: Unknown calling convention -- yet parameter storage is locked */
/* SUPPORTED ANALYST INTERPRETATION; address identity retained. Allocation 0x8c, original
   LiveSamplerApplication vtable. Original source signature is not recovered. */

LiveSamplerApplication_view_009327f0 * sp16_application_factory_0056e7bc(void)

{
  void *pvVar1;
  LiveSamplerApplication_view_009327f0 *pLVar2;
  
  pLVar2 = operator_new(0x8c);
  FUN_007832d0();
  pvVar1 = DAT_0056e8e0;
  pLVar2->main_window = (void *)0x0;
  pLVar2->settings = (void *)0x0;
  pLVar2->primary_vtable = pvVar1;
  pLVar2->secondary_vtable = (void *)((int)pvVar1 + 0x4c);
  *(undefined4 *)&pLVar2->field_0x20 = 0;
  *(undefined4 *)&pLVar2->field_0x24 = 0;
  pLVar2->ui_thread = (void *)0x0;
  pLVar2->processing_graph = (void *)0x0;
  *(undefined4 *)&pLVar2->field_0x30 = 0;
  *(undefined4 *)&pLVar2->field_0x34 = 0;
  *(undefined4 *)&pLVar2->field_0x38 = 0;
  *(undefined4 *)&pLVar2->field_0x3c = 0;
  pLVar2->controller_data_manager = (void *)0x0;
  FUN_0032afa0(&pLVar2->field_0x44);
  *(undefined4 *)&pLVar2->field_0x68 = 0;
  FUN_0050190c(&pLVar2->field_0x6c,0x1000,0x10000);
  signal(0xb,DAT_0056e8e4);
  signal(7,DAT_0056e8e4);
  signal(8,DAT_0056e8e4);
  signal(4,DAT_0056e8e4);
  FUN_0050a49c(DAT_0056e8e8);
  FUN_000c01f4(&pLVar2->field_0x6c);
  return pLVar2;
}

