// Copyright 2026 The Lynx Authors. All rights reserved.
// Licensed under the Apache License Version 2.0 that can be found in the
// LICENSE file in the root directory of this source tree.

// Keep lexical bindings at script scope to exercise global variable writes.
let global_write_value = 0;
let global_write_sum = 0;
for (let global_write_index = 0; global_write_index < 100; global_write_index++) {
    global_write_value = global_write_index;
    global_write_sum += global_write_value;
}
if (global_write_sum !== 4950) throw new Error("global lexical write");

function update_global_write_value() {
    global_write_value = {value: 42};
}
update_global_write_value();
if (global_write_value.value !== 42) throw new Error("global object write");
global_write_value = "replacement";
if (global_write_value !== "replacement") throw new Error("global overwrite");

const global_write_constant = 7;
try {
    global_write_constant = 8;
    throw new Error("missing const error");
} catch (error) {
    if (!(error instanceof TypeError)) throw error;
}
if (global_write_constant !== 7) throw new Error("const changed");

try {
    global_write_tdz = 1;
    throw new Error("missing TDZ error");
} catch (error) {
    if (!(error instanceof ReferenceError)) throw error;
}
let global_write_tdz = 2;
if (global_write_tdz !== 2) throw new Error("lexical initialization");

Object.defineProperty(globalThis, "global_write_readonly", {
    value: 9, writable: false, configurable: true
});
try {
    (0, eval)('"use strict"; global_write_readonly = 10;');
    throw new Error("missing readonly error");
} catch (error) {
    if (!(error instanceof TypeError)) throw error;
}
if (global_write_readonly !== 9) throw new Error("readonly changed");
delete globalThis.global_write_readonly;

var global_write_setter_calls = 0;
Object.defineProperty(globalThis, "global_write_setter", {
    set: function(value) {
        if (value !== 11) throw new Error("setter value");
        global_write_setter_calls++;
    }, configurable: true
});
global_write_setter = 11;
if (global_write_setter_calls !== 1) throw new Error("setter call count");
delete globalThis.global_write_setter;

try {
    (0, eval)('"use strict"; global_write_missing = 1;');
    throw new Error("missing strict reference error");
} catch (error) {
    if (!(error instanceof ReferenceError)) throw error;
}
