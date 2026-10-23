let sum = 0;
for (let i = 0; i < 10000; i++) {
  const value = "primjs-" + (i % 10) + "-benchmark";
  sum += value.slice(7, 8).charCodeAt(0);
}
if (sum !== 525000) throw new Error("strings result: " + sum);
print(sum);
