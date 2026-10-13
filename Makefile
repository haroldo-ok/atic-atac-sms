SDK := vendor/sdk
CC := sdcc
CFLAGS := -mz80 -I$(SDK) --peep-file $(SDK)/peep-rules.txt --opt-code-size
LIBFILES := SMSlib SMSlib_sprite SMSlib_load1bppTiles SMSlib_VRAMmemcpy SMSlib_VRAMmemset
LIBRELS := $(addprefix $(SDK)/obj/,$(addsuffix .rel,$(LIBFILES)))
TESTS := mechanics win characters serf pause hardware rooms weapons trapdoor

all: AticAtac.sms

tools/bin/ihx2sms: $(SDK)/ihx2sms.c
	mkdir -p tools/bin
	gcc -O2 -o $@ $<

tools/bin/smstest: tools/harness/smstest.c tools/harness/z80.c tools/harness/z80.h
	mkdir -p tools/bin
	gcc -O2 -o $@ tools/harness/smstest.c tools/harness/z80.c -lm

$(SDK)/obj/%.rel: $(SDK)/src/%.c $(SDK)/src/SMSlib.h $(SDK)/src/SMSlib_common.c
	mkdir -p $(SDK)/obj
	$(CC) -mz80 -DVDPTYPE_DETECTION -I$(SDK)/src -c $< -o $@

$(SDK)/SMSlib.lib: $(LIBRELS)
	sdar -rc $@ $(LIBRELS)

main.rel: src/main.c gen/assets.h $(SDK)/SMSlib.h
	$(CC) $(CFLAGS) -c $< -o $@

bridge.rel: src/bridge.s
	sdasz80 -plosgff $@ $<

platform.ihx: main.rel bridge.rel $(SDK)/SMSlib.lib $(SDK)/crt0_sms.rel
	$(CC) -mz80 --no-std-crt0 --data-loc 0xC000 --code-loc 0x200 -o $@ $(SDK)/crt0_sms.rel main.rel bridge.rel $(SDK)/SMSlib.lib

platform.sms: platform.ihx tools/bin/ihx2sms
	tools/bin/ihx2sms platform.ihx $@

AticAtac.sms: platform.sms tools/pack_rom.py gen/assets.bin gen/original.bin tools/reference.skool
	python tools/pack_rom.py

playtest: AticAtac.sms tools/bin/smstest
	mkdir -p shots
	@set -e; for test in $(TESTS); do echo "Testing $$test"; tools/bin/smstest AticAtac.sms tests/$$test.txt > shots/$$test-test.log; tail -1 shots/$$test-test.log; done
	python tools/verify_rom.py

assets:
	python tools/convert.py
	python tools/add_food.py
	python tools/add_keys.py
	python tools/add_fall.py

clean:
	rm -f *.rel *.asm *.lst *.sym *.rst *.ihx *.lk *.map *.noi platform.sms AticAtac.sms $(SDK)/SMSlib.lib
	rm -rf $(SDK)/obj tools/bin

.PHONY: all playtest assets clean
