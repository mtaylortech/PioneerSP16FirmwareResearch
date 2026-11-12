/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

/* SUPPORTED ANALYST INTERPRETATION; address identity retained. Called with testmode flag; hardware
   effects unverified. Original source signature is not recovered. */

void sp16_device_initialise_0055659c(int param_1,undefined4 param_2)

{
  undefined4 uVar1;
  int iVar2;
  uint uVar3;
  undefined4 *puVar4;
  void *pvVar5;
  undefined4 *puVar6;
  int iVar7;
  int iVar8;
  uint uVar9;
  int iVar10;
  int iVar11;
  uint in_fpscr;
  float fVar12;
  uint local_70;
  uint local_6c;
  undefined4 local_68;
  undefined4 local_64;
  undefined2 local_60;
  undefined2 local_5e;
  undefined2 local_58;
  undefined2 local_56;
  undefined2 local_50;
  undefined2 local_4e;
  undefined1 auStack_48 [4];
  undefined1 auStack_44 [4];
  undefined1 auStack_40 [4];
  undefined1 auStack_3c [4];
  undefined1 auStack_38 [4];
  undefined1 local_34;
  undefined1 local_33;
  
  iVar2 = *(int *)(param_1 + 8);
  FUN_0055b1a4(iVar2 + 0xac,0,0,0);
  FUN_0055b1a4(iVar2 + 0xd4,1,0,0);
  FUN_0055b1a4(iVar2 + 0xfc,2,0,0);
  FUN_0055b1a4(iVar2 + 0x124,3,0,0);
  FUN_0055b1a4(iVar2 + 0x14c,4,0,0);
  FUN_0055b1a4(iVar2 + 0x174,5,0,0);
  FUN_0055b1a4(iVar2 + 0x19c,6,0,0);
  FUN_0055b1a4(iVar2 + 0x1c4,7,0,0);
  FUN_0055b1a4(iVar2 + 0x1ec,8,0,0);
  FUN_0055b1a4(iVar2 + 0x214,9,0,0);
  FUN_0055b1a4(iVar2 + 0x23c,10,0,0);
  FUN_0055b1a4(iVar2 + 0x264,0xb,0,0);
  FUN_0055b1a4(iVar2 + 0x28c,0xc,0,0);
  FUN_0055b1a4(iVar2 + 0x2b4,0xd,0,0);
  FUN_0055b1a4(iVar2 + 0x2dc,0xe,0,0);
  FUN_0055b1a4(iVar2 + 0x304,0xf,0,0);
  FUN_0055b1a4(iVar2 + 0x32c,0x10,0,0);
  FUN_0055b1a4(iVar2 + 0x3f4,0x15,0,0);
  FUN_0055b1a4(iVar2 + 0x41c,0x16,0,0);
  FUN_0055b1a4(iVar2 + 0x444,0x17,0,0);
  FUN_0055b1a4(iVar2 + 0x46c,0x18,0,0);
  FUN_0055b1a4(iVar2 + 0x494,0x19,0,0);
  FUN_0055b1a4(iVar2 + 0x4bc,0x1a,0,0);
  FUN_0055b1a4(iVar2 + 0x4e4,0x1b,0,0);
  FUN_0055b1a4(iVar2 + 0x50c,0x1c,0,0);
  FUN_0055b1a4(iVar2 + 0x534,0x1d,0,0);
  FUN_0055b1a4(iVar2 + 0x55c,0x1e,0,0);
  FUN_0055b1a4(iVar2 + 0x584,0x1f,0,0);
  FUN_0055b1a4(iVar2 + 0x5ac,0x20,0,0);
  FUN_0055b1a4(iVar2 + 0x5d4,0x21,0,0);
  FUN_0055b1a4(iVar2 + 0x5fc,0x22,0,0);
  FUN_0055b1a4(iVar2 + 0x624,0x23,0,0);
  FUN_0055b1a4(iVar2 + 0x64c,0x24,0,0);
  FUN_0055b1a4(iVar2 + 0x354,0x11,0,0);
  FUN_0055b1a4(iVar2 + 0x37c,0x12,0,0);
  FUN_0055b1a4(iVar2 + 0x3a4,0x13,0,0);
  FUN_0055b1a4(iVar2 + 0x3cc,0x14,0,0);
  iVar7 = 0;
  do {
    iVar8 = iVar7 + 1;
    FUN_0064a3fc(auStack_3c,DAT_0055a7f4);
    FUN_0062d868(auStack_40,iVar8);
    FUN_0062f808(auStack_38,auStack_3c,auStack_40);
    FUN_00663f10(auStack_48,auStack_38);
    FUN_00627f38(auStack_38);
    FUN_00627f38(auStack_40);
    FUN_00627f38(auStack_3c);
    FUN_00627ba0(auStack_44,auStack_48);
    FUN_0068b048(iVar2 + 0xfe0,auStack_44);
    uVar3 = FUN_0061f7c4();
    FUN_006280c8(auStack_44);
    FUN_006280c8(auStack_48);
    if ((int)uVar3 < 0x10) {
      local_70 = 0x10;
LAB_0055a16c:
      uVar3 = 0x36a;
    }
    else {
      local_70 = uVar3;
      if (uVar3 < 0x36a) goto LAB_0055a16c;
    }
    local_6c = uVar3;
    FUN_0055b69c(iVar7 * 0x54 + iVar2 + 0x6ec,iVar7,0,0,&local_70);
    iVar7 = iVar8;
  } while (iVar8 != 0x10);
  FUN_0055c1cc(iVar2 + 0xcf4,0,0,0,0,0);
  FUN_0055c1cc(iVar2 + 0xd5c,1,0,0,0,0);
  FUN_0055c1cc(iVar2 + 0xdc4,2,0,0,0,0);
  iVar11 = 0;
  FUN_0055c1cc(iVar2 + 0xe2c,3,0,0,0,0);
  FUN_0055c1cc(iVar2 + 0xe94,4,0,0,0,0);
  FUN_0055c1cc(iVar2 + 0xefc,5,0,0,0,0);
  FUN_0055c1cc(iVar2 + 0xf64,6,0,0,0,0);
  uVar1 = DAT_0055a7f8;
  puVar4 = operator_new(0x20);
  uVar3 = 0;
  iVar7 = 0;
  pvVar5 = (void *)0x0;
  puVar4[5] = 4;
  *(undefined2 *)(puVar4 + 1) = 0;
  *(undefined2 *)(puVar4 + 6) = 3;
  *(undefined2 *)((int)puVar4 + 6) = 0;
  puVar4[7] = 0x3f800000;
  iVar8 = 4;
  *puVar4 = uVar1;
  puVar4[2] = 0;
  puVar4[3] = 0;
  puVar4[4] = 0;
  do {
    iVar10 = iVar7 + 1;
    if (((int)uVar3 < iVar10) && (uVar9 = iVar10 + iVar10 / 2 + 8U & 0xfffffff8, uVar9 != uVar3)) {
      if ((int)uVar9 < 1) {
        free(pvVar5);
        iVar7 = puVar4[4];
        iVar8 = puVar4[5];
        pvVar5 = (void *)0x0;
        iVar10 = iVar7 + 1;
        puVar4[2] = 0;
        puVar4[3] = uVar9;
      }
      else {
        if (pvVar5 == (void *)0x0) {
          pvVar5 = malloc(uVar9 << 1);
          puVar4[2] = pvVar5;
        }
        else {
          pvVar5 = realloc(pvVar5,uVar9 << 1);
          iVar7 = puVar4[4];
          iVar8 = puVar4[5];
          iVar10 = iVar7 + 1;
          puVar4[2] = pvVar5;
        }
        puVar4[3] = uVar9;
      }
      puVar4[4] = iVar10;
      if ((void *)((int)pvVar5 + iVar7 * 2) != (void *)0x0) {
        *(undefined2 *)((int)pvVar5 + iVar7 * 2) = *(undefined2 *)(puVar4 + 1);
      }
      iVar7 = iVar10;
      if (iVar8 <= iVar11 + 1) break;
    }
    else {
      puVar4[4] = iVar10;
      if ((void *)((int)pvVar5 + iVar7 * 2) != (void *)0x0) {
        *(undefined2 *)((int)pvVar5 + iVar7 * 2) = *(undefined2 *)(puVar4 + 1);
      }
      iVar7 = iVar10;
      if (iVar8 <= iVar11 + 1) break;
    }
    iVar11 = iVar11 + 1;
    uVar3 = puVar4[3];
  } while( true );
  local_60 = 0;
  local_5e = 0x3ff;
  iVar11 = 0;
  fVar12 = (float)VectorSignedToFloat(iVar8,(byte)(in_fpscr >> 0x16) & 3);
  puVar4[7] = 1.0 / (fVar12 + 1.0);
  FUN_0055eea8(iVar2 + 0x674,0,0,puVar4,&local_60,1);
  puVar4 = operator_new(0x20);
  uVar3 = 0;
  iVar7 = 0;
  pvVar5 = (void *)0x0;
  puVar4[5] = 4;
  puVar4[7] = 0x3f800000;
  *(undefined2 *)(puVar4 + 1) = 0;
  *(undefined2 *)(puVar4 + 6) = 3;
  iVar8 = 4;
  *(undefined2 *)((int)puVar4 + 6) = 0;
  *puVar4 = uVar1;
  puVar4[2] = 0;
  puVar4[3] = 0;
  puVar4[4] = 0;
  do {
    iVar10 = iVar7 + 1;
    if (((int)uVar3 < iVar10) && (uVar9 = iVar10 + iVar10 / 2 + 8U & 0xfffffff8, uVar9 != uVar3)) {
      if ((int)uVar9 < 1) {
        free(pvVar5);
        iVar7 = puVar4[4];
        iVar8 = puVar4[5];
        pvVar5 = (void *)0x0;
        iVar10 = iVar7 + 1;
        puVar4[2] = 0;
        puVar4[3] = uVar9;
      }
      else {
        if (pvVar5 == (void *)0x0) {
          pvVar5 = malloc(uVar9 << 1);
          puVar4[2] = pvVar5;
        }
        else {
          pvVar5 = realloc(pvVar5,uVar9 << 1);
          iVar7 = puVar4[4];
          iVar8 = puVar4[5];
          iVar10 = iVar7 + 1;
          puVar4[2] = pvVar5;
        }
        puVar4[3] = uVar9;
      }
      puVar4[4] = iVar10;
      if ((void *)((int)pvVar5 + iVar7 * 2) != (void *)0x0) {
        *(undefined2 *)((int)pvVar5 + iVar7 * 2) = *(undefined2 *)(puVar4 + 1);
      }
      iVar7 = iVar10;
      if (iVar8 <= iVar11 + 1) break;
    }
    else {
      puVar4[4] = iVar10;
      if ((void *)((int)pvVar5 + iVar7 * 2) != (void *)0x0) {
        *(undefined2 *)((int)pvVar5 + iVar7 * 2) = *(undefined2 *)(puVar4 + 1);
      }
      iVar7 = iVar10;
      if (iVar8 <= iVar11 + 1) break;
    }
    iVar11 = iVar11 + 1;
    uVar3 = puVar4[3];
  } while( true );
  local_58 = 0;
  local_56 = 0x3ff;
  iVar11 = 0;
  iVar7 = 0;
  fVar12 = (float)VectorSignedToFloat(iVar8,(byte)(in_fpscr >> 0x16) & 3);
  puVar4[7] = 1.0 / (fVar12 + 1.0);
  FUN_0055eea8(iVar2 + 0x69c,1,0,puVar4,&local_58,1);
  puVar4 = operator_new(0x20);
  uVar3 = 0;
  iVar8 = 4;
  pvVar5 = (void *)0x0;
  *(undefined2 *)(puVar4 + 1) = 0;
  puVar4[7] = 0x3f800000;
  *(undefined2 *)((int)puVar4 + 6) = 0;
  *puVar4 = uVar1;
  puVar4[2] = 0;
  puVar4[3] = 0;
  puVar4[5] = 4;
  *(undefined2 *)(puVar4 + 6) = 0;
  puVar4[4] = 0;
  do {
    iVar10 = iVar7 + 1;
    if (((int)uVar3 < iVar10) && (uVar9 = iVar10 + iVar10 / 2 + 8U & 0xfffffff8, uVar9 != uVar3)) {
      if ((int)uVar9 < 1) {
        free(pvVar5);
        iVar7 = puVar4[4];
        iVar8 = puVar4[5];
        pvVar5 = (void *)0x0;
        iVar10 = iVar7 + 1;
        puVar4[2] = 0;
        puVar4[3] = uVar9;
      }
      else {
        if (pvVar5 == (void *)0x0) {
          pvVar5 = malloc(uVar9 << 1);
          puVar4[2] = pvVar5;
        }
        else {
          pvVar5 = realloc(pvVar5,uVar9 << 1);
          iVar7 = puVar4[4];
          iVar8 = puVar4[5];
          iVar10 = iVar7 + 1;
          puVar4[2] = pvVar5;
        }
        puVar4[3] = uVar9;
      }
      puVar4[4] = iVar10;
      if ((void *)((int)pvVar5 + iVar7 * 2) != (void *)0x0) {
        *(undefined2 *)((int)pvVar5 + iVar7 * 2) = *(undefined2 *)(puVar4 + 1);
      }
      iVar7 = iVar10;
      if (iVar8 <= iVar11 + 1) goto LAB_0055a5cc;
    }
    else {
      puVar4[4] = iVar10;
      if ((void *)((int)pvVar5 + iVar7 * 2) != (void *)0x0) {
        *(undefined2 *)((int)pvVar5 + iVar7 * 2) = *(undefined2 *)(puVar4 + 1);
      }
      iVar7 = iVar10;
      if (iVar8 <= iVar11 + 1) {
LAB_0055a5cc:
        uVar1 = DAT_0055a7fc;
        local_50 = 0;
        local_4e = 0x3ff;
        fVar12 = (float)VectorSignedToFloat(iVar8,(byte)(in_fpscr >> 0x16) & 3);
        puVar4[7] = 1.0 / (fVar12 + 1.0);
        FUN_0055eea8(iVar2 + 0x6c4,2,0,puVar4,&local_50,0);
        local_68 = 0;
        local_64 = 0;
        puVar4 = operator_new(0x28);
        puVar4[5] = 10;
        puVar4[1] = 0;
        puVar4[2] = 0;
        puVar4[3] = 3;
        *(undefined1 *)(puVar4 + 4) = 1;
        *puVar4 = uVar1;
        pvVar5 = malloc(0x28);
        puVar4[6] = pvVar5;
        puVar6 = operator_new(0x28);
        puVar6[1] = 0;
        puVar6[2] = 0;
        puVar6[5] = 10;
        puVar6[3] = 3;
        *(undefined1 *)(puVar6 + 4) = 1;
        *puVar6 = uVar1;
        pvVar5 = malloc(0x28);
        puVar6[6] = pvVar5;
        FUN_0055d5ec(iVar2 + 0xc2c,&local_68,param_2,puVar4,puVar6);
        local_34 = 0;
        local_33 = 0x7f;
        FUN_0055e820(iVar2 + 0xcd0,0,0,0,&local_34);
        FUN_00555cd4(iVar2 + 0xfcc,1);
        FUN_0055803c(iVar2);
        return;
      }
    }
    iVar11 = iVar11 + 1;
    uVar3 = puVar4[3];
  } while( true );
}

