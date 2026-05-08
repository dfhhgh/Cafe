export const sampleProgram = `count recipe brew(count shots) {
    check (shots < 2) {
        bill 1;
    }

    bill shots * brew(shots - 1);
}

count package prices[3] = {10, 20, 30};
coin ready = hot;
emo cup = 'c';

serve << cup;
serve << prices[1];
serve << brew(5);
`;
