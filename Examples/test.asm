%INCLUDE "Along32.inc"
%INCLUDE "Macros_Along.inc"

SECTION .text                           
global  _start                          ; Examples/test

_start:                                 
        mov     eax,[I3]                
        mov     [I4],eax                
        Exit    {0}                     

SECTION .data                           
I0      dd      5                       ; A
B0      dd      -1                      ; B
C0      dd      'C',0                   ; CC
S0      dd      "Explicit Const",0      ; S
L0      dd      1,2                     ; L
I1      dd      4                       ; C
B1      dd      0                       ; D
C1      dd      'C',0                   ; CCC
S1      dd      "Implicit Const",0      ; ST
L1      dd      1,2                     ; LL

SECTION .bss                            
I2      resd    -5                      ; a
B2      resd    -1                      ; b
C2      resd    'c',0                   ; cc
S2      resd    "Explicit Var",0        ; s
L2      resd    1,2                     ; l
I3      resd    -6                      ; c
B3      resd    0                       ; d
C3      resd    'c',0                   ; ccc
S3      resd    "Implicit Var",0        ; st
L3      resd    1,2                     ; ll
B4      resd    -1                      ; E
I4      resd    1                       ; F
L4      resd    1,2                     ; lll
