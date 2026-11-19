/* Naked tail-call stubs. Order must match avrt_proxy.c and avrt_proxy.def.
 * Each stub jumps through its entry in the C global array g_real[]. */
    .text

    .macro STUB name, offset
    .globl \name
\name:
    movq g_real+\offset(%rip), %rax
    jmp *%rax
    .endm

    STUB AvCreateTaskIndex, 0
    STUB AvQuerySystemResponsiveness, 8
    STUB AvQueryTaskIndexValue, 16
    STUB AvRevertMmThreadCharacteristics, 24
    STUB AvRtCreateThreadOrderingGroup, 32
    STUB AvRtCreateThreadOrderingGroupExA, 40
    STUB AvRtCreateThreadOrderingGroupExW, 48
    STUB AvRtDeleteThreadOrderingGroup, 56
    STUB AvRtJoinThreadOrderingGroup, 64
    STUB AvRtLeaveThreadOrderingGroup, 72
    STUB AvRtWaitOnThreadOrderingGroup, 80
    STUB AvSetMmMaxThreadCharacteristicsA, 88
    STUB AvSetMmMaxThreadCharacteristicsW, 96
    STUB AvSetMmThreadCharacteristicsA, 104
    STUB AvSetMmThreadCharacteristicsW, 112
    STUB AvSetMmThreadPriority, 120
    STUB AvSetMultimediaMode, 128
    STUB AvTaskIndexYield, 136
    STUB AvTaskIndexYieldCancel, 144
    STUB AvThreadOpenTaskIndex, 152
