// import React from 'react';

// const AudioPlayerButton = ({ chunkId }) => {
//     const handlePlayAudio = () => {
//         const audioElement = new Audio(`http://localhost:80/audio/${chunkId}.wav`);
//         audioElement.play();
//     };

//     return (
//         <button onClick={handlePlayAudio}>Play</button>
//     );
// };

// export default AudioPlayerButton;
import React from 'react';

const AudioPlayerButton = ({ chunkId }) => {
    const handlePlayAudio = () => {
        const audioElement = new Audio(`http://localhost:7860/audio/${chunkId}.wav`);
        audioElement.play();
    };

    return (
        <button onClick={handlePlayAudio}>Play</button>
    );
};

export default AudioPlayerButton;
