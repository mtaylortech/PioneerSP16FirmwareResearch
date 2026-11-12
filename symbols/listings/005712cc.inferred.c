/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

/* WARNING: Unknown calling convention -- yet parameter storage is locked */
/* SUPPORTED ANALYST INTERPRETATION; address identity retained. Mode bit 0 selects test graph; bits
   1/2 skip normal graph. Audio/MIDI node strings support interpretation. Original source signature
   is not recovered. */

void sp16_build_mode_graph_005712cc(LiveSamplerApplication_view_009327f0 *app,uint mode_flags)

{
  uint *puVar1;
  uint *puVar2;
  char *pcVar3;
  undefined1 *puVar4;
  void *pvVar5;
  int iVar6;
  undefined4 uVar7;
  int *piVar8;
  int iVar9;
  int *piVar10;
  uint uVar11;
  int iVar12;
  undefined8 *puVar13;
  undefined8 *puVar14;
  undefined4 uVar15;
  undefined4 uVar16;
  undefined1 auStack_130 [64];
  undefined8 *local_f0;
  int local_ec;
  int local_e8;
  int local_e0;
  int local_dc;
  undefined4 local_d8;
  undefined4 local_d4;
  undefined4 local_d0;
  undefined4 local_cc;
  undefined4 local_c8;
  undefined4 local_c4;
  undefined4 local_c0;
  undefined4 local_bc;
  undefined4 local_b8;
  undefined4 local_b4;
  undefined4 local_b0;
  int local_ac;
  int local_a8;
  int local_a4;
  int local_a0;
  int local_9c;
  int local_98;
  int local_94;
  undefined4 local_90;
  undefined4 local_8c;
  undefined8 local_88;
  undefined4 local_80;
  undefined4 local_7c;
  undefined4 local_78;
  undefined4 local_74;
  undefined4 local_70;
  undefined4 local_6c;
  undefined4 local_68;
  undefined4 local_64;
  undefined4 local_60;
  undefined4 local_5c;
  undefined4 local_58;
  undefined4 local_54;
  undefined4 local_50;
  undefined4 local_4c;
  undefined4 local_48;
  undefined4 local_44;
  undefined4 local_40;
  undefined4 local_3c;
  undefined4 local_38;
  undefined4 local_34;
  undefined4 local_30;
  undefined4 local_2c;
  undefined4 local_28;
  undefined4 local_24;
  undefined4 local_20;
  undefined4 local_1c;
  
  if ((mode_flags & 1) == 0) {
    if (((mode_flags & 2) == 0) && ((mode_flags & 4) == 0)) {
      local_90 = 0x3f000000;
      local_8c = 0x3f000000;
      local_88 = 0x3f0000003f000000;
      local_80 = 0x3f000000;
      local_7c = 0x3f000000;
      local_d4 = 0xc;
      local_c4 = 1;
      local_c0 = 999;
      local_b0 = 2;
      local_b4 = 0x40;
      local_ac = 1;
      local_a4 = 8;
      local_a8 = 0x100;
      local_a0 = 2;
      local_9c = 8;
      local_d8 = 4;
      local_98 = 0x2c;
      local_d0 = 0x10;
      local_94 = 0x40000000;
      local_cc = 0x10;
      local_c8 = 0x10;
      piVar8 = operator_new(0x758);
      local_bc = 4;
      local_b8 = 0x10;
      memcpy(auStack_130,&local_cc,0x54);
      FUN_001c2cac(piVar8,local_d8,local_d4,local_d0);
      app->processing_graph = piVar8;
    }
    else {
      piVar8 = app->processing_graph;
    }
  }
  else {
    local_30 = 0x3f800000;
    local_2c = 0x3f800000;
    local_28 = 0x3f800000;
    local_24 = 0x3f800000;
    local_20 = 0x3f800000;
    local_1c = 0x3f800000;
    local_34 = 0x3f800000;
    local_74 = 0xc;
    local_64 = 1;
    local_60 = 999;
    local_50 = 2;
    local_54 = 0x40;
    local_4c = 1;
    local_44 = 8;
    local_48 = 0x100;
    local_40 = 2;
    local_3c = 8;
    local_78 = 4;
    local_38 = 0x2c;
    local_70 = 0x10;
    local_6c = 0x10;
    local_68 = 0x10;
    piVar8 = operator_new(0x4f0);
    local_5c = 4;
    local_58 = 0x10;
    memcpy(auStack_130,&local_6c,0x54);
    FUN_0053cf54(piVar8,local_78,local_74,local_70);
    piVar10 = DAT_0057154c;
    iVar9 = *DAT_0057154c;
    if (iVar9 == 0) {
      pthread_mutex_lock(DAT_00571550);
      puVar4 = DAT_00571558;
      pcVar3 = DAT_00571554;
      if ((*piVar10 == 0) && (*DAT_00571554 == '\0')) {
        *DAT_00571554 = '\x01';
        *puVar4 = 1;
        pvVar5 = operator_new(0x3f0);
        FUN_00562370();
        *piVar10 = (int)pvVar5;
        *pcVar3 = '\0';
      }
      pthread_mutex_unlock(DAT_00571550);
      iVar9 = *piVar10;
    }
    if (piVar8 == (int *)0x0) {
      piVar10 = (int *)0x0;
    }
    else {
      piVar10 = piVar8 + 0x125;
    }
    FUN_00562a94(iVar9,piVar10);
    app->processing_graph = piVar8;
  }
  if (piVar8 != (int *)0x0) {
    local_88 = DAT_001b6658;
    FUN_005fab04();
    pvVar5 = operator_new(0x88);
    FUN_005fb6c4(pvVar5,0);
    FUN_0064a3fc(&local_7c,DAT_001b6660);
    iVar9 = FUN_005fdfec(piVar8,pvVar5,0);
    if (iVar9 != 0) {
      FUN_0062d87c(&local_54,*(undefined4 *)(iVar9 + 8));
      FUN_00657374(piVar8 + 0x11b,&local_54,&local_7c);
      FUN_00627f38(&local_54);
    }
    FUN_00627f38(&local_7c);
    pvVar5 = operator_new(0x88);
    FUN_005fb6c4(pvVar5,1);
    FUN_0064a3fc(&local_78,DAT_001b6664);
    iVar6 = FUN_005fdfec(piVar8,pvVar5,0);
    if (iVar6 != 0) {
      FUN_0062d87c(&local_50,*(undefined4 *)(iVar6 + 8));
      FUN_00657374(piVar8 + 0x11b,&local_50,&local_78);
      FUN_00627f38(&local_50);
    }
    FUN_00627f38(&local_78);
    pvVar5 = operator_new(0x88);
    FUN_005fb6c4(pvVar5,2);
    FUN_0064a3fc(&local_74,DAT_001b6668);
    local_e0 = FUN_005fdfec(piVar8,pvVar5,0);
    if (local_e0 != 0) {
      FUN_0062d87c(&local_4c,*(undefined4 *)(local_e0 + 8));
      FUN_00657374(piVar8 + 0x11b,&local_4c,&local_74);
      FUN_00627f38(&local_4c);
    }
    FUN_00627f38(&local_74);
    pvVar5 = operator_new(0x88);
    FUN_005fb6c4(pvVar5,3);
    FUN_0064a3fc(&local_70,DAT_001b666c);
    local_dc = FUN_005fdfec(piVar8,pvVar5,0);
    if (local_dc != 0) {
      FUN_0062d87c(&local_48,*(undefined4 *)(local_dc + 8));
      FUN_00657374(piVar8 + 0x11b,&local_48,&local_70);
      FUN_00627f38(&local_48);
    }
    FUN_00627f38(&local_70);
    pvVar5 = operator_new(0xa8);
    FUN_001b8a00(pvVar5,0);
    local_e8 = piVar8[10];
    piVar8[0xeb] = (int)pvVar5;
    local_f0 = (undefined8 *)piVar8[8];
    local_ec = piVar8[9];
    FUN_005f9e90(pvVar5,0,2);
    iVar12 = piVar8[0xeb];
    FUN_0064a3fc(&local_6c,DAT_001b6670);
    iVar12 = FUN_005fdfec(piVar8,iVar12,0);
    if (iVar12 != 0) {
      FUN_0062d87c(&local_44,*(undefined4 *)(iVar12 + 8));
      FUN_00657374(piVar8 + 0x11b,&local_44,&local_6c);
      FUN_00627f38(&local_44);
    }
    piVar8[0xf1] = iVar12;
    FUN_00627f38(&local_6c);
    piVar10 = piVar8 + 0xf5;
    uVar7 = (**(code **)(**(int **)(piVar8[0x99] + 0x78) + 0x38))();
    local_f0 = (undefined8 *)0x0;
    local_ec = 0;
    FUN_00576c8c(piVar10,2,uVar7,0);
    pvVar5 = operator_new(0x90);
    FUN_001acf14(pvVar5,0,piVar10);
    FUN_0064a3fc(&local_68,DAT_001b6674);
    iVar12 = FUN_005fdfec(piVar8,pvVar5,0);
    if (iVar12 != 0) {
      FUN_0062d87c(&local_40,*(undefined4 *)(iVar12 + 8));
      FUN_00657374(piVar8 + 0x11b,&local_40,&local_68);
      FUN_00627f38(&local_40);
    }
    piVar8[0xf4] = iVar12;
    FUN_00627f38(&local_68);
    pvVar5 = operator_new(0x90);
    FUN_001acf14(pvVar5,1,piVar10);
    FUN_0064a3fc(&local_64,DAT_001b6678);
    iVar12 = FUN_005fdfec(piVar8,pvVar5,0);
    if (iVar12 != 0) {
      FUN_0062d87c(&local_3c,*(undefined4 *)(iVar12 + 8));
      FUN_00657374(piVar8 + 0x11b,&local_3c,&local_64);
      FUN_00627f38(&local_3c);
    }
    piVar8[0xf3] = iVar12;
    FUN_00627f38(&local_64);
    pvVar5 = operator_new(0xa8);
    FUN_001b8a00(pvVar5,0);
    local_e8 = piVar8[10];
    piVar8[0xec] = (int)pvVar5;
    local_f0 = (undefined8 *)piVar8[8];
    local_ec = piVar8[9];
    FUN_005f9e90(pvVar5,0,0);
    iVar12 = piVar8[0xec];
    FUN_0064a3fc(&local_60,DAT_001b667c);
    iVar12 = FUN_005fdfec(piVar8,iVar12,0);
    if (iVar12 != 0) {
      FUN_0062d87c(&local_38,*(undefined4 *)(iVar12 + 8));
      FUN_00657374(piVar8 + 0x11b,&local_38,&local_60);
      FUN_00627f38(&local_38);
    }
    piVar8[0xf2] = iVar12;
    FUN_00627f38(&local_60);
    local_ac = piVar8[0x93];
    local_9c = piVar8[0x97];
    local_b8 = 0x1010101;
    local_b4 = CONCAT13(local_b4._3_1_,0x101);
    local_a8 = piVar8[0x94];
    local_b0 = 7;
    local_90 = 0x1010101;
    local_8c = local_b4;
    local_a4 = piVar8[0x95];
    local_a0 = piVar8[0x96];
    local_98 = piVar8[0x98];
    local_94 = local_ac;
    pvVar5 = operator_new(0x170);
    FUN_001ae7dc(pvVar5,&local_b0);
    uVar7 = DAT_001b6680;
    piVar8[0xee] = (int)pvVar5;
    FUN_0064a3fc(&local_5c,uVar7);
    iVar12 = FUN_005fdfec(piVar8,pvVar5,0);
    if (iVar12 != 0) {
      FUN_0062d87c(&local_34,*(undefined4 *)(iVar12 + 8));
      FUN_00657374(piVar8 + 0x11b,&local_34,&local_5c);
      FUN_00627f38(&local_34);
    }
    piVar8[0xf0] = iVar12;
    FUN_00627f38(&local_5c);
    iVar12 = (**(code **)(*piVar8 + 0xc4))(piVar8);
    uVar7 = *(undefined4 *)(iVar12 + 0x44);
    pvVar5 = operator_new(0x568);
    FUN_001ade60(pvVar5,uVar7);
    uVar7 = DAT_001b6684;
    piVar8[0xed] = (int)pvVar5;
    FUN_0064a3fc(&local_58,uVar7);
    iVar12 = FUN_005fdfec(piVar8,pvVar5,0);
    if (iVar12 != 0) {
      FUN_0062d87c(&local_30,*(undefined4 *)(iVar12 + 8));
      FUN_00657374(piVar8 + 0x11b,&local_30,&local_58);
      FUN_00627f38(&local_30);
    }
    puVar2 = DAT_001b6688;
    piVar8[0xef] = iVar12;
    FUN_00627f38(&local_58);
    uVar7 = *(undefined4 *)(iVar9 + 8);
    if (((*puVar2 & 1) == 0) && (iVar12 = __cxa_guard_acquire(puVar2), iVar12 != 0)) {
      *DAT_001b7254 = DAT_001b71c8;
      __cxa_guard_release(puVar2);
    }
    puVar13 = DAT_001b7250;
    puVar2 = DAT_001b668c;
    uVar16 = *(undefined4 *)(piVar8[0xef] + 8);
    puVar14 = DAT_001b6690;
    if (((*DAT_001b668c & 1) == 0) &&
       (iVar12 = __cxa_guard_acquire(DAT_001b668c), puVar14 = puVar13, iVar12 != 0)) {
      *puVar13 = DAT_001b71c8;
      __cxa_guard_release(puVar2);
    }
    puVar2 = DAT_001b6694;
    local_f0 = puVar14;
    FUN_001b61bc(piVar8,uVar7,DAT_001b6698,uVar16);
    uVar7 = *(undefined4 *)(iVar9 + 8);
    if (((*puVar2 & 1) == 0) && (iVar9 = __cxa_guard_acquire(puVar2), iVar9 != 0)) {
      *DAT_001b724c = DAT_001b71f8;
      __cxa_guard_release(puVar2);
    }
    puVar13 = DAT_001b7248;
    puVar2 = DAT_001b669c;
    uVar16 = *(undefined4 *)(piVar8[0xef] + 8);
    puVar14 = DAT_001b66a0;
    if (((*DAT_001b669c & 1) == 0) &&
       (iVar9 = __cxa_guard_acquire(DAT_001b669c), puVar14 = puVar13, iVar9 != 0)) {
      *puVar13 = DAT_001b71f8;
      __cxa_guard_release(puVar2);
    }
    puVar2 = DAT_001b66a4;
    local_f0 = puVar14;
    FUN_001b61bc(piVar8,uVar7,DAT_001b66a8,uVar16);
    puVar13 = DAT_001b7244;
    uVar16 = *(undefined4 *)(piVar8[0xf4] + 8);
    uVar7 = *(undefined4 *)(piVar8[0xef] + 8);
    puVar14 = DAT_001b66ac;
    if (((*puVar2 & 1) == 0) && (iVar9 = __cxa_guard_acquire(puVar2), puVar14 = puVar13, iVar9 != 0)
       ) {
      *puVar13 = DAT_001b71f0;
      __cxa_guard_release(puVar2);
    }
    puVar2 = DAT_001b66b0;
    local_f0 = puVar14;
    FUN_001b61bc(piVar8,uVar16,&local_88,uVar7);
    uVar7 = *(undefined4 *)(piVar8[0xf0] + 8);
    if (((*puVar2 & 1) == 0) &&
       (iVar9 = __cxa_guard_acquire(puVar2), puVar1 = DAT_001b671c, iVar9 != 0)) {
      *DAT_001b6718 = DAT_001b71c8;
      __cxa_guard_release(puVar2);
      uVar11 = *puVar1;
      uVar16 = *(undefined4 *)(iVar6 + 8);
      puVar13 = DAT_001b7200;
      puVar14 = DAT_001b7200;
    }
    else {
      uVar16 = *(undefined4 *)(iVar6 + 8);
      uVar11 = *DAT_001b671c;
      puVar13 = DAT_001b66b4;
      puVar1 = DAT_001b671c;
      puVar14 = DAT_001b7200;
    }
    DAT_001b7200 = puVar14;
    if (((uVar11 & 1) == 0) && (iVar9 = __cxa_guard_acquire(puVar1), puVar13 = puVar14, iVar9 != 0))
    {
      *puVar14 = DAT_001b71c8;
      __cxa_guard_release(puVar1);
    }
    puVar2 = DAT_001b66b8;
    local_f0 = puVar13;
    FUN_001b61bc(piVar8,uVar7,DAT_001b6718,uVar16);
    uVar7 = *(undefined4 *)(piVar8[0xf0] + 8);
    if (((*puVar2 & 1) == 0) &&
       (iVar9 = __cxa_guard_acquire(puVar2), puVar1 = DAT_001b723c, iVar9 != 0)) {
      *DAT_001b7238 = DAT_001b71f8;
      __cxa_guard_release(puVar2);
      uVar11 = *puVar1;
      uVar16 = *(undefined4 *)(iVar6 + 8);
      puVar13 = DAT_001b7240;
      puVar14 = DAT_001b7240;
    }
    else {
      uVar16 = *(undefined4 *)(iVar6 + 8);
      uVar11 = *DAT_001b66bc;
      puVar1 = DAT_001b66bc;
      puVar13 = DAT_001b66c0;
      puVar14 = DAT_001b7240;
    }
    DAT_001b7240 = puVar14;
    if (((uVar11 & 1) == 0) && (iVar9 = __cxa_guard_acquire(puVar1), puVar13 = puVar14, iVar9 != 0))
    {
      *puVar14 = DAT_001b71f8;
      __cxa_guard_release(puVar1);
    }
    puVar2 = DAT_001b66c4;
    local_f0 = puVar13;
    FUN_001b61bc(piVar8,uVar7,DAT_001b66c8,uVar16);
    uVar7 = *(undefined4 *)(piVar8[0xf0] + 8);
    if (((*puVar2 & 1) == 0) &&
       (iVar9 = __cxa_guard_acquire(puVar2), puVar1 = DAT_001b7230, iVar9 != 0)) {
      *DAT_001b722c = DAT_001b71f0;
      __cxa_guard_release(puVar2);
      uVar11 = *puVar1;
      uVar16 = *(undefined4 *)(iVar6 + 8);
      puVar13 = DAT_001b7234;
      puVar14 = DAT_001b7234;
    }
    else {
      uVar16 = *(undefined4 *)(iVar6 + 8);
      uVar11 = *DAT_001b66cc;
      puVar1 = DAT_001b66cc;
      puVar13 = DAT_001b66d0;
      puVar14 = DAT_001b7234;
    }
    DAT_001b7234 = puVar14;
    if (((uVar11 & 1) == 0) && (iVar9 = __cxa_guard_acquire(puVar1), puVar13 = puVar14, iVar9 != 0))
    {
      *puVar14 = DAT_001b71f0;
      __cxa_guard_release(puVar1);
    }
    puVar2 = DAT_001b66d4;
    local_f0 = puVar13;
    FUN_001b61bc(piVar8,uVar7,DAT_001b66d8,uVar16);
    uVar7 = *(undefined4 *)(piVar8[0xf0] + 8);
    if (((*puVar2 & 1) == 0) &&
       (iVar9 = __cxa_guard_acquire(puVar2), puVar1 = DAT_001b7224, iVar9 != 0)) {
      *DAT_001b7220 = DAT_001b71e8;
      __cxa_guard_release(puVar2);
      uVar11 = *puVar1;
      uVar16 = *(undefined4 *)(iVar6 + 8);
      puVar13 = DAT_001b7228;
      puVar14 = DAT_001b7228;
    }
    else {
      uVar16 = *(undefined4 *)(iVar6 + 8);
      uVar11 = *DAT_001b66dc;
      puVar1 = DAT_001b66dc;
      puVar13 = DAT_001b66e0;
      puVar14 = DAT_001b7228;
    }
    DAT_001b7228 = puVar14;
    if (((uVar11 & 1) == 0) && (iVar9 = __cxa_guard_acquire(puVar1), puVar13 = puVar14, iVar9 != 0))
    {
      *puVar14 = DAT_001b71e8;
      __cxa_guard_release(puVar1);
    }
    puVar2 = DAT_001b66e4;
    local_f0 = puVar13;
    FUN_001b61bc(piVar8,uVar7,DAT_001b66e8,uVar16);
    uVar7 = *(undefined4 *)(piVar8[0xf0] + 8);
    if (((*puVar2 & 1) == 0) &&
       (iVar9 = __cxa_guard_acquire(puVar2), puVar1 = DAT_001b7218, iVar9 != 0)) {
      *DAT_001b7214 = DAT_001b71e0;
      __cxa_guard_release(puVar2);
      uVar11 = *puVar1;
      uVar16 = *(undefined4 *)(iVar6 + 8);
      puVar13 = DAT_001b721c;
      puVar14 = DAT_001b721c;
    }
    else {
      uVar16 = *(undefined4 *)(iVar6 + 8);
      uVar11 = *DAT_001b66ec;
      puVar1 = DAT_001b66ec;
      puVar13 = DAT_001b66f0;
      puVar14 = DAT_001b721c;
    }
    DAT_001b721c = puVar14;
    if (((uVar11 & 1) == 0) && (iVar9 = __cxa_guard_acquire(puVar1), puVar13 = puVar14, iVar9 != 0))
    {
      *puVar14 = DAT_001b71e0;
      __cxa_guard_release(puVar1);
    }
    puVar2 = DAT_001b66f4;
    local_f0 = puVar13;
    FUN_001b61bc(piVar8,uVar7,DAT_001b66f8,uVar16);
    uVar7 = *(undefined4 *)(piVar8[0xf0] + 8);
    if (((*puVar2 & 1) == 0) &&
       (iVar9 = __cxa_guard_acquire(puVar2), puVar1 = DAT_001b720c, iVar9 != 0)) {
      *DAT_001b7208 = DAT_001b71d8;
      __cxa_guard_release(puVar2);
      uVar11 = *puVar1;
      uVar16 = *(undefined4 *)(iVar6 + 8);
      puVar13 = DAT_001b7210;
      puVar14 = DAT_001b7210;
    }
    else {
      uVar16 = *(undefined4 *)(iVar6 + 8);
      uVar11 = *DAT_001b66fc;
      puVar1 = DAT_001b66fc;
      puVar13 = DAT_001b6700;
      puVar14 = DAT_001b7210;
    }
    DAT_001b7210 = puVar14;
    if (((uVar11 & 1) == 0) && (iVar9 = __cxa_guard_acquire(puVar1), puVar13 = puVar14, iVar9 != 0))
    {
      *puVar14 = DAT_001b71d8;
      __cxa_guard_release(puVar1);
    }
    puVar2 = DAT_001b6704;
    local_f0 = puVar13;
    FUN_001b61bc(piVar8,uVar7,DAT_001b6708,uVar16);
    uVar7 = *(undefined4 *)(piVar8[0xf0] + 8);
    if (((*puVar2 & 1) == 0) && (iVar9 = __cxa_guard_acquire(puVar2), iVar9 != 0)) {
      *DAT_001b7204 = DAT_001b71d0;
      __cxa_guard_release(puVar2);
    }
    local_f0 = &local_88;
    FUN_001b61bc(piVar8,uVar7,DAT_001b670c,*(undefined4 *)(piVar8[0xf3] + 8));
    uVar16 = *(undefined4 *)(local_e0 + 8);
    uVar15 = *(undefined4 *)(piVar8[0xf1] + 8);
    uVar7 = *DAT_001b6710;
    FUN_0064a3fc(&local_2c,DAT_001b6714);
    local_f0 = (undefined8 *)uVar7;
    iVar9 = FUN_005fae80(piVar8,uVar16,uVar7,uVar15);
    if (iVar9 != 0) {
      local_f0 = (undefined8 *)uVar7;
      FUN_005ff2c4(piVar8,uVar16,uVar7,uVar15);
    }
    FUN_00627f38(&local_2c);
    uVar16 = *(undefined4 *)(piVar8[0xf1] + 8);
    uVar15 = *(undefined4 *)(piVar8[0xf4] + 8);
    FUN_0064a3fc(&local_2c,DAT_001b6714);
    local_f0 = (undefined8 *)uVar7;
    iVar9 = FUN_005fae80(piVar8,uVar16,uVar7,uVar15);
    if (iVar9 != 0) {
      local_f0 = (undefined8 *)uVar7;
      FUN_005ff2c4(piVar8,uVar16,uVar7,uVar15);
    }
    FUN_00627f38(&local_2c);
    uVar16 = *(undefined4 *)(piVar8[0xf4] + 8);
    uVar15 = *(undefined4 *)(piVar8[0xef] + 8);
    FUN_0064a3fc(&local_2c,DAT_001b6714);
    local_f0 = (undefined8 *)uVar7;
    iVar9 = FUN_005fae80(piVar8,uVar16,uVar7,uVar15);
    if (iVar9 != 0) {
      local_f0 = (undefined8 *)uVar7;
      FUN_005ff2c4(piVar8,uVar16,uVar7,uVar15);
    }
    FUN_00627f38(&local_2c);
    uVar16 = *(undefined4 *)(piVar8[0xf0] + 8);
    uVar15 = *(undefined4 *)(piVar8[0xf3] + 8);
    FUN_0064a3fc(&local_2c,DAT_001b6714);
    local_f0 = (undefined8 *)uVar7;
    iVar9 = FUN_005fae80(piVar8,uVar16,uVar7,uVar15);
    if (iVar9 != 0) {
      local_f0 = (undefined8 *)uVar7;
      FUN_005ff2c4(piVar8,uVar16,uVar7,uVar15);
    }
    FUN_00627f38(&local_2c);
    uVar16 = *(undefined4 *)(piVar8[0xf3] + 8);
    uVar15 = *(undefined4 *)(piVar8[0xf2] + 8);
    FUN_0064a3fc(&local_2c,DAT_001b6714);
    local_f0 = (undefined8 *)uVar7;
    iVar9 = FUN_005fae80(piVar8,uVar16,uVar7,uVar15);
    if (iVar9 != 0) {
      local_f0 = (undefined8 *)uVar7;
      FUN_005ff2c4(piVar8,uVar16,uVar7,uVar15);
    }
    FUN_00627f38(&local_2c);
    uVar16 = *(undefined4 *)(piVar8[0xf2] + 8);
    uVar15 = *(undefined4 *)(local_dc + 8);
    FUN_0064a3fc(&local_2c,DAT_001b6714);
    local_f0 = (undefined8 *)uVar7;
    iVar9 = FUN_005fae80(piVar8,uVar16,uVar7,uVar15);
    if (iVar9 != 0) {
      local_f0 = (undefined8 *)uVar7;
      FUN_005ff2c4(piVar8,uVar16,uVar7,uVar15);
    }
    FUN_00627f38(&local_2c);
    (**(code **)(*piVar8 + 0xdc))(piVar8);
    return;
  }
  return;
}

