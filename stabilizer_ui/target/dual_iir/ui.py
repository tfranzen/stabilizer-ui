from PyQt6 import QtWidgets
from stabilizer import DEFAULT_DUAL_IIR_SAMPLE_PERIOD
from stabilizer.stream import Parser, AdcDecoder, DacDecoder

from . import *
from .topics import StabilizerSettings, UiSettings

from ...ui import AbstractUiWindow
from ...mqtt import NetworkAddress, UiMqttConfig
from ...iir.channel_settings import ChannelSettings
from ...stream.fft_scope import FftScope

from ...utils import mega


#
# Parameters for the FNC ui.
#

DEFAULT_WINDOW_SIZE = (1200, 600)
DEFAULT_DAC_PLOT_YRANGE = (-1, 1)
DEFAULT_ADC_PLOT_YRANGE = (-1, 1)

#: Interval between scope plot updates, in seconds.
#: PyQt's drawing speed limits value.
SCOPE_UPDATE_PERIOD = 0.05  # 20 fps


class UiWindow(AbstractUiWindow):

    def __init__(self, title: str = "Dual IIR"):
        super().__init__()
        self.setWindowTitle(title)
        print([DEFAULT_DUAL_IIR_SAMPLE_PERIOD,SAMPLE_PERIOD_REDUCTION])
        # Set main window layout
        splitter = QtWidgets.QSplitter(self)
        self.setCentralWidget(splitter)

        # Create UI for channel settings.
        self.channels = [
            ChannelSettings(DEFAULT_DUAL_IIR_SAMPLE_PERIOD*SAMPLE_PERIOD_REDUCTION) for _ in range(NUM_CHANNELS)
        ]

        self.channelTabWidget = QtWidgets.QTabWidget()
        for i, channel in enumerate(self.channels):
            self.channelTabWidget.addTab(channel, f"Channel {i}")
        splitter.addWidget(self.channelTabWidget)

        # Create UI for FFT scope.
        streamParser = Parser([AdcDecoder(), DacDecoder()])
        self.fftScopeWidget = FftScope(streamParser, DEFAULT_DUAL_IIR_SAMPLE_PERIOD*SAMPLE_PERIOD_REDUCTION)
        splitter.addWidget(self.fftScopeWidget)

        for i in range(NUM_CHANNELS):
            self.fftScopeWidget.graphics_view.getItem(
                0, i).setYRange(*DEFAULT_ADC_PLOT_YRANGE)
            self.fftScopeWidget.graphics_view.getItem(
                1, i).setYRange(*DEFAULT_DAC_PLOT_YRANGE)


        for i, channel in enumerate(self.channels):
            channel.connect_to_lockpoint(i, self.fftScopeWidget.update_lockpoint)
            channel.connect_to_offset(i, self.fftScopeWidget.update_inputoffset)

        self.fftScopeWidget.lockpoint_callback = self.lockpointclick

        # Disable mouse wheel scrolling on spinboxes to prevent accidental changes
        spinboxes = self.channelTabWidget.findChildren(QtWidgets.QDoubleSpinBox)
        for box in spinboxes:
            box.wheelEvent = lambda *event: None

        self.resize(*DEFAULT_WINDOW_SIZE)

    def update_stream(self, payload):
        self.fftScopeWidget.update(payload)


    def lockpointclick(self, i, x):
        self.channels[i].lockpointBox.setValue(x)

    def set_mqtt_configs(self, stream_target: NetworkAddress):
        """ Link the UI widgets to the MQTT topic tree"""

        # `ui/#` are only used by the UI, the others by both UI and stabilizer
        settings_map = {
            StabilizerSettings.stream_target.path():
            UiMqttConfig(
                [],
                lambda _: stream_target._asdict(),
                lambda _w, _v: stream_target._asdict(),
            )
        }

        for ch in range(NUM_CHANNELS):
            settings_map[StabilizerSettings.afes[ch].path()] = UiMqttConfig(
                [self.channels[ch].afeGainBox])

            settings_map[StabilizerSettings.input_offset[ch].path()] = UiMqttConfig(
                [self.channels[ch].inputOffsetBox])


            settings_map[StabilizerSettings.fgens[ch].amplitude.path()] = UiMqttConfig(
                [self.channels[ch].fgenAmpBox])
            
            settings_map[StabilizerSettings.fgens[ch].signal.path()] = UiMqttConfig(
                [self.channels[ch].fgenWaveformBox])

            settings_map[StabilizerSettings.fgens[ch].frequency.path()] = UiMqttConfig(
                [self.channels[ch].fgenFreqBox])

            settings_map[StabilizerSettings.lockboxes[ch].enable.path()] = UiMqttConfig(
                [self.channels[ch].LockBoxEnableCheckBox])

            settings_map[StabilizerSettings.lockboxes[ch].lockpoint.path()] = UiMqttConfig(
                [self.channels[ch].lockpointBox])

            settings_map[StabilizerSettings.lockboxes[ch].state_request.path()] = UiMqttConfig(
                [self.channels[ch].lockstateBox])


            settings_map[StabilizerSettings.attenuation_ins[ch].path()] = UiMqttConfig(
                [self.channels[ch].ddsInAttenuationBox])
            settings_map[StabilizerSettings.attenuation_outs[ch].path()] = UiMqttConfig(
                [self.channels[ch].ddsOutAttenuationBox])

            settings_map[StabilizerSettings.amplitude_dds_ins[ch].path()] = UiMqttConfig(
                [self.channels[ch].ddsInAmplitudeBox])
            settings_map[StabilizerSettings.amplitude_dds_outs[ch].path()] = UiMqttConfig(
                [self.channels[ch].ddsOutAmplitudeBox])

            settings_map[StabilizerSettings.phase_dds_ins[ch].path()] = UiMqttConfig(
                [self.channels[ch].ddsInPhaseBox])
            settings_map[StabilizerSettings.phase_dds_outs[ch].path()] = UiMqttConfig(
                [self.channels[ch].ddsOutPhaseBox])

            settings_map[StabilizerSettings.frequency_dds_outs[ch].path()] = UiMqttConfig(
                [self.channels[ch].ddsOutFrequencyBox], *mega)
            settings_map[StabilizerSettings.frequency_dds_ins[ch].path()] = UiMqttConfig(
                [self.channels[ch].ddsInFrequencyBox], *mega)

            settings_map[UiSettings.dds_io_link_checkboxes[ch].path()] = UiMqttConfig(
                [self.channels[ch].ddsIoFreqLinkCheckBox])

            # IIR settings
            for iir in range(NUM_IIR_FILTERS_PER_CHANNEL):
                iirWidget = self.channels[ch].iir_widgets[iir]
                iir_topic = UiSettings.iirs[ch][iir]

                iirWidget.set_mqtt_configs(settings_map, iir_topic)

        return settings_map
