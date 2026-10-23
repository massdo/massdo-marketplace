// ⌘ plus one key anywhere: opens the Claude session that has waited on you longest (agent-queue plugin).
// A Carbon hot key needs no Accessibility permission. A LaunchAgent starts it at login (see install.sh).
// Usage: hotkey [character], the key that types `character` with ⌘; "@" by default.
import AppKit
import Carbon

let script = NSString(string: "~/.claude/agent-queue/next.js").expandingTildeInPath
let character = CommandLine.arguments.dropFirst().first ?? "@"

func log(_ text: String) {
    FileHandle.standardError.write(Data("agent-queue: \(text)\n".utf8))
}

// The key that types `character` on the current layout: "@" is the top-left key on a French Mac.
func keyCode(typing character: String) -> UInt32? {
    guard let source = TISCopyCurrentKeyboardLayoutInputSource()?.takeRetainedValue(),
          let property = TISGetInputSourceProperty(source, kTISPropertyUnicodeKeyLayoutData) else { return nil }
    let data = Unmanaged<CFData>.fromOpaque(property).takeUnretainedValue() as Data

    return data.withUnsafeBytes { raw -> UInt32? in
        guard let layout = raw.bindMemory(to: UCKeyboardLayout.self).baseAddress else { return nil }
        for code in UInt16(0)..<128 {
            var deadKeys: UInt32 = 0
            var chars = [UniChar](repeating: 0, count: 4)
            var length = 0
            let status = UCKeyTranslate(layout, code, UInt16(kUCKeyActionDown), 0, UInt32(LMGetKbdType()),
                                        OptionBits(kUCKeyTranslateNoDeadKeysBit), &deadKeys, chars.count, &length, &chars)
            if status == noErr, String(utf16CodeUnits: chars, count: length) == character { return UInt32(code) }
        }

        return nil
    }
}

func openNext() {
    let task = Process()
    task.executableURL = URL(fileURLWithPath: "/usr/bin/osascript")
    task.arguments = ["-l", "JavaScript", script]
    do {
        try task.run()
    } catch {
        log("could not run \(script): \(error)")
    }
}

var spec = EventTypeSpec(eventClass: OSType(kEventClassKeyboard), eventKind: UInt32(kEventHotKeyPressed))
InstallEventHandler(GetApplicationEventTarget(), { _, _, _ in
    openNext()

    return noErr
}, 1, &spec, nil, nil)

guard let code = keyCode(typing: character) else {
    log("no key types \(character) without a modifier on this keyboard layout")
    exit(1)
}
var hotKey: EventHotKeyRef?
let status = RegisterEventHotKey(code, UInt32(cmdKey), EventHotKeyID(signature: OSType(0x6167_7471), id: 1),
                                 GetApplicationEventTarget(), 0, &hotKey)
guard status == noErr else {
    log("⌘\(character) is already taken (\(status))")
    exit(1)
}
log("⌘\(character) bound to key code \(code)")

NSApplication.shared.setActivationPolicy(.accessory)
NSApplication.shared.run()
