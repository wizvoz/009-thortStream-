; ============================================================================
; Filename:   dora_scraper_helper.ahk
; Author:     Simon C, assisted by Dora
; Version:    3.0
; Date:       2025-08-12
; Aim:        An AutoHotkey macro to automate the scrolling of long Gemini
;             conversations during the scraping process.
; ============================================================================

; --- CONFIGURATION ---
; Hotkey: Press F8 to run the scroll-and-confirm sequence.
TotalBursts := 10      ; How many times to repeat the scroll-and-pause cycle.
KeysPerBurst := 20     ; How many 'Page Up' presses to send in each burst.
PauseAfterBurst := 1500; The pause duration in milliseconds (1500 = 1.5 seconds).
; ---

F8::
    ; Step 1: Activate Firefox and click to ensure focus.
    WinActivate, ahk_exe firefox.exe
    WinWaitActive, ahk_exe firefox.exe, , 2
    Click 
    Sleep, 200

    ; Step 2: Begin the "Burst and Pause" scrolling loop.
    Loop, %TotalBursts%
    {
        ; Inner loop for the burst of key presses
        Loop, %KeysPerBurst%
        {
            Send, {PgUp}
            Sleep, 50 ; Small delay between each keypress
        }
        ; Long pause after the burst to allow content to load
        Sleep, %PauseAfterBurst%
    }
    
    ; Step 3: Pause for 2 seconds for the page to finally settle.
    Sleep, 2000 
    
    ; Step 4: Activate the terminal window.
    WinActivate, ahk_exe mintty.exe
    WinWaitActive, ahk_exe mintty.exe, , 2
    
    ; Step 5: Send 'Enter' to continue the Python script.
    Send, {Enter}
return
