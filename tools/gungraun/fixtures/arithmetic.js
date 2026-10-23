// Fixed work with an observable result; no timing loop.
let sum = 0;
for (let i = 0; i < 100000; i++) sum = (sum + (i * 17 % 101)) | 0;
if (sum !== 4999861) throw new Error("arithmetic result: " + sum);
print(sum);
