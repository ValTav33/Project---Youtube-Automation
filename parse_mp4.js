const fs = require('fs');
const buffer = fs.readFileSync('/tmp/scene_4.mp4');
let offset = 0;
while (offset < buffer.length) {
    const size = buffer.readUInt32BE(offset);
    const type = buffer.toString('ascii', offset + 4, offset + 8);
    if (type === 'moov') {
        let moovOffset = offset + 8;
        while (moovOffset < offset + size) {
            const innerSize = buffer.readUInt32BE(moovOffset);
            const innerType = buffer.toString('ascii', moovOffset + 4, moovOffset + 8);
            if (innerType === 'mvhd') {
                const version = buffer.readUInt8(moovOffset + 8);
                const timeScaleOffset = version === 1 ? 28 : 20;
                const durationOffset = version === 1 ? 32 : 24;
                const timeScale = buffer.readUInt32BE(moovOffset + 8 + timeScaleOffset);
                const duration = version === 1 ? Number(buffer.readBigUInt64BE(moovOffset + 8 + durationOffset)) : buffer.readUInt32BE(moovOffset + 8 + durationOffset);
                console.log('Duration:', duration / timeScale, 'seconds');
                process.exit(0);
            }
            moovOffset += innerSize;
        }
    }
    offset += size;
}
