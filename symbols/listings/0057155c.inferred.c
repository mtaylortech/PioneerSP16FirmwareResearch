/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

/* WARNING: Unknown calling convention -- yet parameter storage is locked */
/* SUPPORTED ANALYST INTERPRETATION; address identity retained. Mode/graph-dependent helper objects;
   relationships inferred. Original source signature is not recovered. */

void sp16_wire_graph_controllers_0057155c(LiveSamplerApplication_view_009327f0 *app,uint mode_flags)

{
  int *piVar1;
  int *piVar2;
  char *pcVar3;
  undefined1 *puVar4;
  void *pvVar5;
  undefined4 uVar6;
  int *piVar7;
  void *pvVar8;
  uint uVar9;
  int iVar10;
  int iVar11;
  int iVar12;
  int iVar13;
  
  piVar7 = DAT_00571cf0;
  if (app->processing_graph == (void *)0x0) {
    return;
  }
  if ((mode_flags & 1) != 0) {
    return;
  }
  iVar11 = *DAT_00571cf0;
  if (iVar11 == 0) {
    pthread_mutex_lock(DAT_00571d04);
    puVar4 = DAT_00571d18;
    pcVar3 = DAT_00571d14;
    if ((*piVar7 == 0) && (*DAT_00571d14 == '\0')) {
      *DAT_00571d14 = '\x01';
      *puVar4 = 1;
      pvVar5 = operator_new(0xc);
      FUN_00556044();
      *piVar7 = (int)pvVar5;
      *pcVar3 = '\0';
    }
    pthread_mutex_unlock(DAT_00571d04);
    iVar11 = *piVar7;
  }
  piVar1 = DAT_00571cf4;
  iVar10 = *DAT_00571cf4;
  if (iVar10 == 0) {
    pthread_mutex_lock(DAT_00571d08);
    puVar4 = DAT_00571d10;
    pcVar3 = DAT_00571d0c;
    if ((*piVar1 == 0) && (*DAT_00571d0c == '\0')) {
      *DAT_00571d0c = '\x01';
      *puVar4 = 1;
      pvVar5 = operator_new(0x3f0);
      FUN_00562370();
      *piVar1 = (int)pvVar5;
      *pcVar3 = '\0';
    }
    pthread_mutex_unlock(DAT_00571d08);
    iVar10 = *piVar1;
  }
  piVar2 = DAT_00571cf8;
  iVar12 = *DAT_00571cf8;
  if (iVar12 == 0) {
    pthread_mutex_lock(DAT_00571d00);
    pcVar3 = DAT_00571d1c;
    if (((*piVar2 == 0) && (*DAT_00571d1c == '\0')) && (*DAT_00571d20 == '\0')) {
      *DAT_00571d20 = '\x01';
      *pcVar3 = '\x01';
      pvVar5 = operator_new(0x170);
      FUN_0037fba8();
      *piVar2 = (int)pvVar5;
      *pcVar3 = '\0';
    }
    pthread_mutex_unlock(DAT_00571d00);
    iVar12 = *piVar2;
    iVar13 = 0;
    if (iVar12 != 0) goto LAB_005715b4;
  }
  else {
LAB_005715b4:
    iVar13 = iVar12 + 0x14;
  }
  pvVar5 = operator_new(0x1e0);
  FUN_00564fec(pvVar5,(int)app->processing_graph + 0x200,iVar11,iVar10,iVar13);
  iVar11 = *piVar7;
  *(void **)&app->field_0x20 = pvVar5;
  if (iVar11 == 0) {
    pthread_mutex_lock(DAT_00571d04);
    puVar4 = DAT_00571d18;
    pcVar3 = DAT_00571d14;
    if ((*DAT_00571cf0 == 0) && (*DAT_00571d14 == '\0')) {
      *DAT_00571d14 = '\x01';
      *puVar4 = 1;
      pvVar5 = operator_new(0xc);
      FUN_00556044();
      *piVar7 = (int)pvVar5;
      *pcVar3 = '\0';
    }
    pthread_mutex_unlock(DAT_00571d04);
    iVar11 = *piVar7;
  }
  iVar10 = *piVar1;
  if (iVar10 == 0) {
    pthread_mutex_lock(DAT_00571d08);
    puVar4 = DAT_00571d10;
    pcVar3 = DAT_00571d0c;
    if ((*DAT_00571cf4 == 0) && (*DAT_00571d0c == '\0')) {
      *DAT_00571d0c = '\x01';
      *puVar4 = 1;
      pvVar5 = operator_new(0x3f0);
      FUN_00562370();
      *piVar1 = (int)pvVar5;
      *pcVar3 = '\0';
    }
    pthread_mutex_unlock(DAT_00571d08);
    iVar10 = *piVar1;
  }
  pvVar5 = operator_new(0x48);
  FUN_00566b80(pvVar5,iVar11,iVar10);
  iVar11 = *(int *)&app->field_0x20;
  *(void **)&app->field_0x24 = pvVar5;
  if (iVar11 == 0) goto LAB_00571740;
  iVar10 = *piVar2;
  iVar12 = iVar11;
  if (iVar10 == 0) {
    pthread_mutex_lock(DAT_00571d00);
    pcVar3 = DAT_00571d1c;
    if (((*DAT_00571cf8 == 0) && (*DAT_00571d1c == '\0')) && (*DAT_00571d20 == '\0')) {
      *DAT_00571d20 = '\x01';
      *pcVar3 = '\x01';
      pvVar5 = operator_new(0x170);
      FUN_0037fba8();
      *piVar2 = (int)pvVar5;
      *pcVar3 = '\0';
    }
    pthread_mutex_unlock(DAT_00571d00);
    iVar10 = *piVar2;
    if (iVar10 != 0) {
      iVar12 = *(int *)&app->field_0x20;
      goto LAB_00571630;
    }
    iVar12 = *(int *)&app->field_0x20;
    iVar10 = 0;
  }
  else {
LAB_00571630:
    iVar10 = iVar10 + 0x14;
  }
  pvVar5 = app->processing_graph;
  *(int *)(iVar11 + 0x110) = iVar10;
  uVar6 = (**(code **)(*(int *)((int)pvVar5 + 0x200) + 0x3c))((int)pvVar5 + 0x200);
  iVar10 = *piVar2;
  iVar11 = *(int *)&app->field_0x20;
  *(undefined4 *)(iVar12 + 0x10c) = uVar6;
  if (iVar10 == 0) {
    pthread_mutex_lock(DAT_00571d00);
    pcVar3 = DAT_00571d1c;
    if (((*DAT_00571cf8 == 0) && (*DAT_00571d1c == '\0')) && (*DAT_00571d20 == '\0')) {
      *DAT_00571d20 = '\x01';
      *pcVar3 = '\x01';
      pvVar5 = operator_new(0x170);
      FUN_0037fba8();
      *piVar2 = (int)pvVar5;
      *pcVar3 = '\0';
    }
    pthread_mutex_unlock(DAT_00571d00);
    iVar10 = *piVar2;
  }
  iVar13 = *(int *)(iVar11 + 0x140);
  iVar12 = iVar13 + 1;
  if (((int)*(uint *)(iVar11 + 0x13c) < iVar12) &&
     (uVar9 = iVar12 + iVar12 / 2 + 8U & 0xfffffff8, *(uint *)(iVar11 + 0x13c) != uVar9)) {
    pvVar5 = *(void **)(iVar11 + 0x138);
    if ((int)uVar9 < 1) {
      free(pvVar5);
      iVar13 = *(int *)(iVar11 + 0x140);
      pvVar5 = (void *)0x0;
      *(uint *)(iVar11 + 0x13c) = uVar9;
      *(undefined4 *)(iVar11 + 0x138) = 0;
      iVar12 = iVar13 + 1;
    }
    else {
      if (pvVar5 == (void *)0x0) {
        pvVar5 = malloc(uVar9 << 2);
        *(void **)(iVar11 + 0x138) = pvVar5;
      }
      else {
        pvVar5 = realloc(pvVar5,uVar9 << 2);
        iVar13 = *(int *)(iVar11 + 0x140);
        iVar12 = iVar13 + 1;
        *(void **)(iVar11 + 0x138) = pvVar5;
      }
      *(uint *)(iVar11 + 0x13c) = uVar9;
    }
  }
  else {
    pvVar5 = *(void **)(iVar11 + 0x138);
  }
  *(int *)(iVar11 + 0x140) = iVar12;
  if ((void *)((int)pvVar5 + iVar13 * 4) != (void *)0x0) {
    *(int *)((int)pvVar5 + iVar13 * 4) = iVar10;
  }
  piVar7 = (int *)(**(code **)(*(int *)((int)app->processing_graph + 0x200) + 0xc))
                            ((int)app->processing_graph + 0x200);
  if (piVar7 != (int *)0x0) {
    iVar11 = *(int *)&app->field_0x20;
    uVar6 = (**(code **)(*piVar7 + 0x40))();
    iVar12 = *(int *)(iVar11 + 0x140);
    iVar10 = iVar12 + 1;
    if (((int)*(uint *)(iVar11 + 0x13c) < iVar10) &&
       (uVar9 = iVar10 + iVar10 / 2 + 8U & 0xfffffff8, *(uint *)(iVar11 + 0x13c) != uVar9)) {
      pvVar5 = *(void **)(iVar11 + 0x138);
      if ((int)uVar9 < 1) {
        free(pvVar5);
        iVar12 = *(int *)(iVar11 + 0x140);
        pvVar5 = (void *)0x0;
        *(uint *)(iVar11 + 0x13c) = uVar9;
        *(undefined4 *)(iVar11 + 0x138) = 0;
        iVar10 = iVar12 + 1;
      }
      else {
        if (pvVar5 == (void *)0x0) {
          pvVar5 = malloc(uVar9 << 2);
          *(void **)(iVar11 + 0x138) = pvVar5;
        }
        else {
          pvVar5 = realloc(pvVar5,uVar9 << 2);
          iVar12 = *(int *)(iVar11 + 0x140);
          iVar10 = iVar12 + 1;
          *(void **)(iVar11 + 0x138) = pvVar5;
        }
        *(uint *)(iVar11 + 0x13c) = uVar9;
      }
    }
    else {
      pvVar5 = *(void **)(iVar11 + 0x138);
    }
    *(int *)(iVar11 + 0x140) = iVar10;
    if ((void *)((int)pvVar5 + iVar12 * 4) != (void *)0x0) {
      *(undefined4 *)((int)pvVar5 + iVar12 * 4) = uVar6;
    }
  }
  iVar11 = *(int *)&app->field_0x20;
  pvVar5 = app->settings;
  iVar10 = *(int *)(iVar11 + 0x140);
  if (pvVar5 != (void *)0x0) {
    pvVar5 = (void *)((int)pvVar5 + 0x14);
  }
  iVar12 = iVar10 + 1;
  if (((int)*(uint *)(iVar11 + 0x13c) < iVar12) &&
     (uVar9 = iVar12 + iVar12 / 2 + 8U & 0xfffffff8, *(uint *)(iVar11 + 0x13c) != uVar9)) {
    pvVar8 = *(void **)(iVar11 + 0x138);
    if ((int)uVar9 < 1) {
      free(pvVar8);
      iVar10 = *(int *)(iVar11 + 0x140);
      pvVar8 = (void *)0x0;
      *(undefined4 *)(iVar11 + 0x138) = 0;
      iVar12 = iVar10 + 1;
    }
    else if (pvVar8 == (void *)0x0) {
      pvVar8 = malloc(uVar9 << 2);
      *(void **)(iVar11 + 0x138) = pvVar8;
    }
    else {
      pvVar8 = realloc(pvVar8,uVar9 << 2);
      iVar10 = *(int *)(iVar11 + 0x140);
      iVar12 = iVar10 + 1;
      *(void **)(iVar11 + 0x138) = pvVar8;
    }
    *(uint *)(iVar11 + 0x13c) = uVar9;
  }
  else {
    pvVar8 = *(void **)(iVar11 + 0x138);
  }
  *(int *)(iVar11 + 0x140) = iVar12;
  piVar7 = DAT_00571cfc;
  if ((void *)((int)pvVar8 + iVar10 * 4) != (void *)0x0) {
    *(void **)((int)pvVar8 + iVar10 * 4) = pvVar5;
  }
  iVar10 = *(int *)&app->field_0x20;
  iVar12 = *(int *)(iVar10 + 0x140);
  iVar11 = 0;
  if (*piVar7 != -0x20) {
    iVar11 = *piVar7 + 0xf4;
  }
  iVar13 = iVar12 + 1;
  if (((int)*(uint *)(iVar10 + 0x13c) < iVar13) &&
     (uVar9 = iVar13 + iVar13 / 2 + 8U & 0xfffffff8, *(uint *)(iVar10 + 0x13c) != uVar9)) {
    pvVar5 = *(void **)(iVar10 + 0x138);
    if ((int)uVar9 < 1) {
      free(pvVar5);
      iVar12 = *(int *)(iVar10 + 0x140);
      pvVar5 = (void *)0x0;
      *(undefined4 *)(iVar10 + 0x138) = 0;
      iVar13 = iVar12 + 1;
    }
    else if (pvVar5 == (void *)0x0) {
      pvVar5 = malloc(uVar9 << 2);
      *(void **)(iVar10 + 0x138) = pvVar5;
    }
    else {
      pvVar5 = realloc(pvVar5,uVar9 << 2);
      iVar12 = *(int *)(iVar10 + 0x140);
      iVar13 = iVar12 + 1;
      *(void **)(iVar10 + 0x138) = pvVar5;
    }
    *(uint *)(iVar10 + 0x13c) = uVar9;
  }
  else {
    pvVar5 = *(void **)(iVar10 + 0x138);
  }
  *(int *)(iVar10 + 0x140) = iVar13;
  if ((void *)((int)pvVar5 + iVar12 * 4) != (void *)0x0) {
    *(int *)((int)pvVar5 + iVar12 * 4) = iVar11;
  }
  pvVar5 = *(void **)&app->field_0x24;
LAB_00571740:
  if (pvVar5 != (void *)0x0) {
    uVar6 = (**(code **)(*(int *)((int)app->processing_graph + 0x200) + 0x3c))
                      ((int)app->processing_graph + 0x200);
    *(undefined4 *)((int)pvVar5 + 0x2c) = uVar6;
  }
  return;
}

