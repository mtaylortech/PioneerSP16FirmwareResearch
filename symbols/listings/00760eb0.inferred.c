/* INFERRED PSEUDOCODE. Check original instructions; names/types may be wrong. No execution in this task. */

void FUN_00760eb0(int param_1,byte param_2,byte param_3)

{
  *(byte *)(param_1 + 0x68) =
       *(byte *)(param_1 + 0x68) & 0xe7 | ((param_2 ^ 1) & 1) << 3 | (param_3 & 1) << 4;
  return;
}

