#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <wchar.h>

static BOOL CALLBACK show_login(HWND window, LPARAM unused)
{
    (void)unused;
    DWORD pid = 0;
    GetWindowThreadProcessId(window, &pid);
    HANDLE process = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, FALSE, pid);
    WCHAR path[32768] = {0};
    DWORD length = 32768;
    if (process) {
        QueryFullProcessImageNameW(process, 0, path, &length);
        CloseHandle(process);
    }
    RECT bounds = {0};
    GetWindowRect(window, &bounds);
    if (wcsstr(path, L"\\GameViewer\\bin\\GameViewer.exe") &&
        bounds.right - bounds.left > 400 && bounds.bottom - bounds.top > 400) {
        ShowWindow(window, SW_RESTORE);
        SetForegroundWindow(window);
        RedrawWindow(window, NULL, NULL, RDW_INVALIDATE | RDW_UPDATENOW | RDW_ALLCHILDREN);
    }
    return TRUE;
}

int main(void)
{
    EnumWindows(show_login, 0);
    return 0;
}
