// Fake backend for trying the UI before the real endpoints exist (VITE_USE_MOCK=true).
const sleep = (ms, signal) =>
  new Promise((resolve, reject) => {
    const timer = setTimeout(resolve, ms);
    signal?.addEventListener(
      "abort",
      () => {
        clearTimeout(timer);
        reject(new DOMException("Aborted", "AbortError"));
      },
      { once: true }
    );
  });

export async function mockUpload(file) {
  await sleep(1200);
  return { doc_id: "mock-doc", filename: file.name, pages: 3, chunks: 6 };
}

export async function mockAsk(_docId, question, signal) {
  await sleep(1400, signal);
  if (/ceo|salary|stock|ipo/i.test(question)) {
    return { grounded: false, answer: "I couldn't find this in the document.", citations: [] };
  }
  return {
    grounded: true,
    answer:
      "The solar panels have a 10 year product warranty [1]. The inverter is covered separately for 5 years, and the battery for 8 years [1]. Damage from unauthorized modifications is not covered [2].",
    citations: [
      {
        id: 1, chunk_id: 3, page: 2, score: 2.7,
        text: "Aurora solar panels are covered by a 10 year product warranty. The inverter carries a separate 5 year warranty, and the AuroraCell battery is covered for 8 years.",
      },
      {
        id: 2, chunk_id: 4, page: 2, score: 1.1,
        text: "Damage caused by unauthorized modifications or by cyclones above category two is not covered by the warranty.",
      },
    ],
  };
}
