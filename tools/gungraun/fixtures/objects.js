let sum = 0;
for (let i = 0; i < 10000; i++) {
  const value = {x: i, y: i + 1, z: i + 2};
  sum += value.x + value.y + value.z;
}
if (sum !== 150015000) throw new Error("objects result: " + sum);
print(sum);
