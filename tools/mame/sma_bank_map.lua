-- Black-box map of the NEO-SMA bank register: writes every 16-bit value to $PD_BANK_REG
-- (0x2FFFE4 by default) and samples what the 68000 then sees in the P2 window (0x200000-0x2FFFFF).
--
-- Output ($PD_TRACE, sma_bank_map.txt by default), one line per value:
--   <value> <hex of 16 bytes at 0x200000 + k * 0x10000, k = 0..15>
-- (bytes in 68000 order). tools/sma_banks.py locates every sample in the program region.
-- Also checks that read taps work in the window: "TAPS <reads seen>" at the end.

local cpu = manager.machine.devices[":maincpu"]
local mem = cpu.spaces["program"]
local reg = tonumber(os.getenv("PD_BANK_REG") or "2FFFE4", 16)
local tap_reads = 0
bank_rtap = mem:install_read_tap(0x200000, 0x2FFFFF, "pd_bank_r", function(offset, data, mask)
    tap_reads = tap_reads + 1
end)

bank_frame = emu.add_machine_frame_notifier(function()
    if manager.machine.screens[":screen"]:frame_number() ~= 2 then return end
    local f = io.open(os.getenv("PD_TRACE") or "sma_bank_map.txt", "w")
    for v = 0, 0xFFFF do
        mem:write_u16(reg, v)
        local parts = { string.format("%04X ", v) }
        for k = 0, 15 do
            local base = 0x200000 + k * 0x10000
            for i = 0, 15, 2 do parts[#parts + 1] = string.format("%04X", mem:read_u16(base + i)) end
        end
        f:write(table.concat(parts), "\n")
    end
    f:write(string.format("TAPS %d\n", tap_reads))
    f:close()
    manager.machine:exit()
end)
