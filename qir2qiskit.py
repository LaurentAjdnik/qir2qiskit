from typing import cast

from pyqir.generator import BasicQisBuilder, SimpleModule
from pyqir.parser import QirModule, QirQisCallInstr

print("\n== Set up circuit (Bernstein-Vazirani algorithm) ==")

sm = SimpleModule("qir2qiskit", 7, 6)
builder = BasicQisBuilder(sm.builder)

# Set first 6 qubits to |+>
builder.h(sm.qubits[0])
builder.h(sm.qubits[1])
builder.h(sm.qubits[2])
builder.h(sm.qubits[3])
builder.h(sm.qubits[4])
builder.h(sm.qubits[5])

# Set ancilla qubit to |->
builder.h(sm.qubits[6])
builder.z(sm.qubits[6])

# Apply oracle
builder.cx(sm.qubits[1], sm.qubits[6])
builder.cx(sm.qubits[3], sm.qubits[6])
builder.cx(sm.qubits[5], sm.qubits[6])

# Apply Hadamard to the first 6 qubits
builder.h(sm.qubits[5])
builder.h(sm.qubits[4])
builder.h(sm.qubits[3])
builder.h(sm.qubits[2])
builder.h(sm.qubits[1])
builder.h(sm.qubits[0])

# Measure the first 6 qubits
builder.m(sm.qubits[0], sm.results[0])
builder.m(sm.qubits[1], sm.results[1])
builder.m(sm.qubits[2], sm.results[2])
builder.m(sm.qubits[3], sm.results[3])
builder.m(sm.qubits[4], sm.results[4])
builder.m(sm.qubits[5], sm.results[5])

print("\n== Display resulting readable QIR ==")

print(sm.ir())

print("\n== Save to file (bitcode and readable) ==")


with open("qir2qiskit.bc", "wb") as bitcode_file:
    bitcode_file.write(bytes(sm.bitcode()))
with open("qir2qiskit.ll", "w") as readable_file:
    readable_file.write(sm.ir())

print("\n== Read and parse bitcode ==")

qir_module = QirModule("qir2qiskit.bc")

print("\n== Rebuild Qiskit source ==")

nb_qubits = 0
nb_bits = 0
source = ""

for instr in qir_module.functions[0].blocks[0].instructions:
    if isinstance(instr, QirQisCallInstr):
        instr = cast(QirQisCallInstr, instr)
        if instr.func_name == "__quantum__qis__cnot__body":
            qubit_control = instr.func_args[0].value
            qubit_target = instr.func_args[1].value
            if qubit_control > nb_qubits:
                nb_qubits = qubit_control
            if qubit_target > nb_qubits:
                nb_qubits = qubit_target
            source += f"qc.cx({qubit_control}, {qubit_target})\n"
        if instr.func_name == "__quantum__qis__h__body":
            qubit = instr.func_args[0].value
            if qubit > nb_qubits:
                nb_qubits = qubit
            source += f"qc.h({qubit})\n"
        if instr.func_name == "__quantum__qis__m__body":
            qubit = instr.func_args[0].value
            bit = int(instr.output_name.replace("result", ""))
            if qubit > nb_qubits:
                nb_qubits = qubit
            if bit > nb_bits:
                nb_bits = bit
            source += f"qc.measure({qubit}, {bit})\n"
        if instr.func_name == "__quantum__qis__z__body":
            qubit = instr.func_args[0].value
            if qubit > nb_qubits:
                nb_qubits = qubit
            source += f"qc.z({qubit})\n"

source = f"qc = QuantumCircuit({nb_qubits+1}, {nb_bits+1})\n\n" + source
source = "from qiskit import Aer, execute, QuantumCircuit\n\n" + source

source += "job = execute(qc, Aer.get_backend('qasm_simulator'), shots=1024)\n\n"
source += "counts = job.result().get_counts(qc)\n"
source += "print(counts)\n"

print(source)
exec(source)
